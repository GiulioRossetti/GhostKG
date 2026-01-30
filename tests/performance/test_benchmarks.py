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
from ghost_kg import AgentManager, AgentCache
from ghost_kg.storage import KnowledgeDB


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
    
    def test_benchmark_node_insertions(self, benchmark):
        """Benchmark node insertion performance."""
        
        def insert_nodes():
            for i in range(100):
                self.db.upsert_node(
                    owner_id="test_agent",
                    node_id=f"node_{i}",
                    fsrs_state=None,
                    timestamp=None
                )
        
        # Run benchmark
        result = benchmark(insert_nodes)
        
        # Verify all nodes were inserted
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE owner_id = 'test_agent'")
        count = cursor.fetchone()[0]
        assert count == 100
    
    def test_benchmark_edge_insertions(self, benchmark):
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
        
        # Run benchmark
        result = benchmark(insert_edges)
        
        # Verify edges were inserted
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM edges WHERE owner_id = 'test_agent'")
        count = cursor.fetchone()[0]
        assert count == 90  # 10 * 9 (no self-loops)
    
    def test_benchmark_query_by_owner(self, benchmark):
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
        
        # Run benchmark
        result = benchmark(query_nodes)
        assert len(result) == 20  # 100 / 5
    
    def test_benchmark_temporal_query(self, benchmark):
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
        
        # Run benchmark
        result = benchmark(query_recent)
        assert len(result) == 20


class TestCachingPerformance:
    """Benchmark caching performance."""
    
    def test_benchmark_cache_hit(self, benchmark):
        """Benchmark cache hit performance."""
        cache = AgentCache(max_size=256, enabled=True)
        
        # Pre-populate cache
        cache.put_context("Alice", "climate", "Context data about climate...")
        
        def get_cached():
            return cache.get_context("Alice", "climate")
        
        # Run benchmark
        result = benchmark(get_cached)
        assert result == "Context data about climate..."
    
    def test_benchmark_cache_miss(self, benchmark):
        """Benchmark cache miss performance."""
        cache = AgentCache(max_size=256, enabled=True)
        
        def get_uncached():
            return cache.get_context("Alice", "nonexistent")
        
        # Run benchmark
        result = benchmark(get_uncached)
        assert result is None
    
    def test_benchmark_cache_eviction(self, benchmark):
        """Benchmark cache with eviction."""
        cache = AgentCache(max_size=10, enabled=True)
        
        def fill_and_overflow():
            # Fill cache beyond max_size
            for i in range(20):
                cache.put_context(f"Agent_{i}", "topic", f"context_{i}")
        
        # Run benchmark
        benchmark(fill_and_overflow)
        
        # Verify cache size is at max
        stats = cache.get_stats()
        assert stats["context_entries"] <= 10


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
        if hasattr(self, 'manager'):
            self.manager.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_benchmark_agent_creation(self, benchmark):
        """Benchmark agent creation."""
        
        def create_agent():
            agent_name = f"Agent_{time.time()}"
            self.manager.create_agent(agent_name)
            return agent_name
        
        # Run benchmark
        result = benchmark(create_agent)
        assert result is not None
    
    def test_benchmark_content_absorption(self, benchmark):
        """Benchmark content absorption (fast mode)."""
        
        # Create agent
        self.manager.create_agent("TestAgent")
        
        def absorb():
            self.manager.absorb_content(
                agent_name="TestAgent",
                content="This is test content about climate change.",
                author="Author",
                triplets=[("climate", "related_to", "change")],
                fast_mode=True
            )
        
        # Run benchmark
        benchmark(absorb)
    
    def test_benchmark_context_retrieval(self, benchmark):
        """Benchmark context retrieval."""
        
        # Create agent and add some data
        self.manager.create_agent("TestAgent")
        for i in range(10):
            self.manager.absorb_content(
                agent_name="TestAgent",
                content=f"Content {i} about climate.",
                author="Author",
                triplets=[("climate", "related_to", f"topic_{i}")],
                fast_mode=True
            )
        
        def get_context():
            return self.manager.get_context("TestAgent", "climate")
        
        # Run benchmark
        result = benchmark(get_context)
        assert "climate" in result.lower() or "CLIMATE" in result


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
        if hasattr(self, 'manager'):
            self.manager.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_benchmark_multi_round_conversation(self, benchmark):
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
                    triplets=[("technology", "discussed_in", f"round_{round_num}")],
                    fast_mode=True
                )
                
                # Alice generates response (simulated)
                response = f"Response to round {round_num}"
                
                # Update Alice's KG with response
                self.manager.update_with_response(
                    agent_name="Alice",
                    response_text=response,
                    context=context,
                    triplets=[("Alice", "responded", f"round_{round_num}")],
                    fast_mode=True
                )
        
        # Run benchmark
        benchmark(conversation)


if __name__ == "__main__":
    # Run benchmarks
    pytest.main([__file__, "-v", "--benchmark-only"])
