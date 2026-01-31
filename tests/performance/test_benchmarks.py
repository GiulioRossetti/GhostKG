"""
Performance benchmarks for GhostKG.

These benchmarks measure the performance of core operations to:
1. Establish baselines
2. Measure improvements from optimizations
3. Identify performance bottlenecks
4. Ensure regressions don't occur

Run with: pytest tests/performance/test_benchmarks.py -v
"""

import pytest
import time
import os
import tempfile
from ghost_kg import AgentManager, AgentCache, KnowledgeDB


class TestDatabasePerformance:
    """Benchmark database operations."""
    
    def setup_method(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = KnowledgeDB(self.db_path)
    
    def teardown_method(self):
        """Clean up test database."""
        if hasattr(self, 'db'):
            self.db.conn.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_benchmark_node_insertions(self):
        """Benchmark node insertion performance."""
        
        def insert_nodes():
            for i in range(100):
                self.db.upsert_node(
                    owner_id="test_agent",
                    node_id=f"node_{i}",
                    fsrs_state=None,
                    timestamp=None
                )
        
        # Time the operation
        start = time.time()
        insert_nodes()
        elapsed = time.time() - start
        
        # Verify all nodes were inserted
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE owner_id = 'test_agent'")
        count = cursor.fetchone()[0]
        assert count == 100
        
        # Basic performance check (should complete in reasonable time)
        assert elapsed < 5.0, f"Node insertion took too long: {elapsed}s"
    
    def test_benchmark_edge_insertions(self):
        """Benchmark edge insertion performance."""
        
        # Pre-create nodes
        for i in range(10):
            self.db.upsert_node(f"test_agent", f"node_{i}")
        
        def insert_edges():
            for i in range(10):
                for j in range(10):
                    if i != j:
                        self.db.add_relation(
                            owner_id="test_agent",
                            source=f"node_{i}",
                            target=f"node_{j}",
                            relation="related_to",
                            sentiment=0.5
                        )
        
        # Time the operation
        start = time.time()
        insert_edges()
        elapsed = time.time() - start
        
        # Verify edges were inserted
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM edges WHERE owner_id = 'test_agent'")
        count = cursor.fetchone()[0]
        assert count == 90  # 10 * 9 (no self-loops)
        
        # Basic performance check
        assert elapsed < 5.0, f"Edge insertion took too long: {elapsed}s"
    
    def test_benchmark_query_by_owner(self):
        """Benchmark querying nodes by owner."""
        
        # Pre-create data
        for i in range(100):
            self.db.upsert_node(f"agent_{i % 5}", f"node_{i}")
        
        def query_nodes():
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT * FROM nodes WHERE owner_id = 'agent_0'
            """)
            return cursor.fetchall()
        
        # Time the operation
        start = time.time()
        result = query_nodes()
        elapsed = time.time() - start
        
        assert len(result) == 20  # 100 / 5
        
        # Basic performance check
        assert elapsed < 1.0, f"Query took too long: {elapsed}s"
    
    def test_benchmark_temporal_query(self):
        """Benchmark temporal queries on edges."""
        
        # Pre-create data
        for i in range(10):
            self.db.upsert_node(f"test_agent", f"node_{i}")
        
        for i in range(50):
            self.db.add_relation(
                owner_id="test_agent",
                source=f"node_{i % 10}",
                target=f"node_{(i + 1) % 10}",
                relation="related",
                sentiment=0.0
            )
        
        def query_recent():
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT * FROM edges 
                WHERE owner_id = 'test_agent'
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            return cursor.fetchall()
        
        # Time the operation
        start = time.time()
        result = query_recent()
        elapsed = time.time() - start
        
        # Should return 20 results (or 10 if there are fewer unique edges)
        # Note: With 10 nodes and no self-loops, we have 10*9=90 total, 
        # but with modulo math we get duplicates, so expect around 10 unique
        assert len(result) >= 10
        
        # Basic performance check
        assert elapsed < 1.0, f"Temporal query took too long: {elapsed}s"


class TestCachingPerformance:
    """Benchmark caching performance."""
    
    def test_benchmark_cache_hit(self):
        """Benchmark cache hit performance."""
        cache = AgentCache(max_size=256, enabled=True)
        
        # Pre-populate cache
        cache.put_context("Alice", "climate", "Context data about climate...")
        
        def get_cached():
            return cache.get_context("Alice", "climate")
        
        # Time the operation
        start = time.time()
        for _ in range(1000):
            result = get_cached()
        elapsed = time.time() - start
        
        assert result == "Context data about climate..."
        
        # Basic performance check
        assert elapsed < 0.1, f"Cache hits took too long: {elapsed}s"
    
    def test_benchmark_cache_miss(self):
        """Benchmark cache miss performance."""
        cache = AgentCache(max_size=256, enabled=True)
        
        def get_uncached():
            return cache.get_context("Alice", "nonexistent")
        
        # Time the operation
        start = time.time()
        for _ in range(1000):
            result = get_uncached()
        elapsed = time.time() - start
        
        assert result is None
        
        # Basic performance check
        assert elapsed < 0.1, f"Cache misses took too long: {elapsed}s"
    
    def test_benchmark_cache_eviction(self):
        """Benchmark cache with eviction."""
        cache = AgentCache(max_size=10, enabled=True)
        
        def fill_and_overflow():
            # Fill cache beyond max_size
            for i in range(20):
                cache.put_context(f"Agent_{i}", "topic", f"context_{i}")
        
        # Time the operation
        start = time.time()
        fill_and_overflow()
        elapsed = time.time() - start
        
        # Verify cache size is at max
        stats = cache.get_stats()
        assert stats["context_entries"] <= 10
        
        # Basic performance check
        assert elapsed < 1.0, f"Cache eviction took too long: {elapsed}s"


class TestAgentManagerPerformance:
    """Benchmark AgentManager operations."""
    
    def setup_method(self):
        """Set up test manager."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.manager = AgentManager(db_path=self.db_path)
    
    def teardown_method(self):
        """Clean up."""
        # Manager doesn't have a close method
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_benchmark_agent_creation(self):
        """Benchmark agent creation."""
        
        def create_agent():
            agent_name = f"Agent_{time.time()}"
            self.manager.create_agent(agent_name)
            return agent_name
        
        # Time the operation
        start = time.time()
        for _ in range(10):
            result = create_agent()
        elapsed = time.time() - start
        
        assert result is not None
        
        # Basic performance check
        assert elapsed < 5.0, f"Agent creation took too long: {elapsed}s"
    
    def test_benchmark_content_absorption(self):
        """Benchmark content absorption."""
        
        # Create agent
        self.manager.create_agent("TestAgent")
        
        def absorb():
            self.manager.absorb_content(
                agent_name="TestAgent",
                content="This is test content about climate change.",
                author="Author",
                triplets=[("climate", "related_to", "change")]
            )
        
        # Time the operation
        start = time.time()
        for _ in range(10):
            absorb()
        elapsed = time.time() - start
        
        # Basic performance check
        assert elapsed < 5.0, f"Content absorption took too long: {elapsed}s"
    
    def test_benchmark_context_retrieval(self):
        """Benchmark context retrieval."""
        
        # Create agent and add some data
        self.manager.create_agent("TestAgent")
        for i in range(10):
            self.manager.absorb_content(
                agent_name="TestAgent",
                content=f"Content {i} about climate.",
                author="Author",
                triplets=[("climate", "related_to", f"topic_{i}")]
            )
        
        def get_context():
            return self.manager.get_context("TestAgent", "climate")
        
        # Time the operation
        start = time.time()
        for _ in range(10):
            result = get_context()
        elapsed = time.time() - start
        
        assert "climate" in result.lower() or "CLIMATE" in result
        
        # Basic performance check
        assert elapsed < 5.0, f"Context retrieval took too long: {elapsed}s"


class TestEndToEndPerformance:
    """Benchmark end-to-end workflows."""
    
    def setup_method(self):
        """Set up test manager."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.manager = AgentManager(db_path=self.db_path)
    
    def teardown_method(self):
        """Clean up."""
        # Manager doesn't have a close method
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_benchmark_multi_round_conversation(self):
        """Benchmark multi-round conversation workflow."""
        
        def conversation():
            # Create two agents
            self.manager.create_agent("Alice")
            self.manager.create_agent("Bob")
            
            # Multi-round interaction
            for round_num in range(5):
                # Alice processes content
                context = self.manager.process_and_get_context(
                    agent_name="Alice",
                    topic="technology",
                    text=f"Technology discussion round {round_num}",
                    author="Bob",
                    triplets=[("technology", "discussed_in", f"round_{round_num}")]
                )
                
                # Alice generates response (simulated)
                response = f"Response to round {round_num}"
                
                # Update Alice's KG with response (relation, target, sentiment)
                self.manager.update_with_response(
                    agent_name="Alice",
                    response=response,
                    context=context,
                    triplets=[("responded", f"round_{round_num}", 0.5)]
                )
        
        # Time the operation
        start = time.time()
        conversation()
        elapsed = time.time() - start
        
        # Basic performance check
        assert elapsed < 10.0, f"Multi-round conversation took too long: {elapsed}s"


if __name__ == "__main__":
    # Run benchmarks
    pytest.main([__file__, "-v"])
