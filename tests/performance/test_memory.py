"""Performance tests for memory management."""
import pytest
import datetime
import time
from ghost_kg import AgentManager, Rating


@pytest.fixture
def manager(tmp_path):
    """Create agent manager with temp database."""
    db_path = tmp_path / "test_memory.db"
    return AgentManager(str(db_path))


class TestMemoryPerformance:
    """Test memory management performance."""
    
    def test_large_knowledge_base_query(self, manager):
        """Test querying performance with large knowledge base."""
        agent_name = "MemoryAgent"
        agent = manager.create_agent(agent_name)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        manager.set_agent_time(agent_name, now)
        
        # Insert 1000 triplets
        start = time.time()
        for i in range(1000):
            manager.learn_triplet(
                agent_name,
                f"entity{i}",
                "relates_to",
                f"concept{i}",
                rating=Rating.Good
            )
        insert_time = time.time() - start
        
        # Query should be fast even with 1000 triplets
        start = time.time()
        context = manager.get_context(agent_name, "entity500")
        query_time = time.time() - start
        
        # Assertions about performance
        assert insert_time < 10.0, f"Insertion took too long: {insert_time}s"
        assert query_time < 1.0, f"Query took too long: {query_time}s"
        
        # Verify data is there
        assert "entity" in context.lower() or "concept" in context.lower()
    
    def test_memory_decay_calculation_performance(self, manager):
        """Test that FSRS memory decay calculations are efficient."""
        agent_name = "DecayAgent"
        agent = manager.create_agent(agent_name)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        manager.set_agent_time(agent_name, now)
        
        # Learn 100 triplets
        for i in range(100):
            manager.learn_triplet(
                agent_name,
                f"topic{i}",
                "is",
                "interesting",
                rating=Rating.Good
            )
        
        # Advance time and re-learn (triggering decay calculations)
        later = now + datetime.timedelta(days=7)
        manager.set_agent_time(agent_name, later)
        
        start = time.time()
        for i in range(100):
            manager.learn_triplet(
                agent_name,
                f"topic{i}",
                "is",
                "interesting",
                rating=Rating.Easy
            )
        review_time = time.time() - start
        
        # Reviews should be fast
        assert review_time < 2.0, f"Review took too long: {review_time}s"
    
    def test_context_generation_with_many_memories(self, manager):
        """Test context generation performance with many stored memories."""
        agent_name = "ContextAgent"
        agent = manager.create_agent(agent_name)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        manager.set_agent_time(agent_name, now)
        
        # Create diverse knowledge base
        topics = ["AI", "climate", "economics", "politics", "science"]
        for topic in topics:
            for i in range(20):
                manager.learn_triplet(
                    agent_name,
                    topic,
                    "relates_to",
                    f"{topic}_concept_{i}",
                    rating=Rating.Good
                )
        
        # Get context for each topic
        start = time.time()
        for topic in topics:
            context = manager.get_context(agent_name, topic)
            assert len(context) > 0
        total_time = time.time() - start
        
        # Should be able to generate 5 contexts quickly
        assert total_time < 2.0, f"Context generation took too long: {total_time}s"
    
    def test_absorb_content_performance(self, manager):
        """Test performance of absorbing content with triplets."""
        agent_name = "AbsorbAgent"
        agent = manager.create_agent(agent_name)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        manager.set_agent_time(agent_name, now)
        
        # Absorb 100 messages
        start = time.time()
        for i in range(100):
            manager.absorb_content(
                agent_name,
                f"Message {i} about topic",
                author=f"User{i % 10}",
                triplets=[(f"Message{i}", "is_about", "topic")]
            )
        absorb_time = time.time() - start
        
        # Should process 100 messages quickly
        assert absorb_time < 5.0, f"Absorbing 100 messages took too long: {absorb_time}s"
    
    def test_memory_growth_over_time(self, manager):
        """Test that memory usage grows linearly with knowledge base size."""
        agent_name = "GrowthAgent"
        agent = manager.create_agent(agent_name)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        manager.set_agent_time(agent_name, now)
        
        # Add memories in batches and time each batch
        batch_times = []
        for batch in range(5):
            start = time.time()
            for i in range(100):
                idx = batch * 100 + i
                manager.learn_triplet(
                    agent_name,
                    f"entity{idx}",
                    "is",
                    f"concept{idx}",
                    rating=Rating.Good
                )
            batch_time = time.time() - start
            batch_times.append(batch_time)
        
        # Each batch should take similar time (linear growth, not exponential)
        avg_time = sum(batch_times) / len(batch_times)
        for batch_time in batch_times:
            # Allow 50% variance
            assert abs(batch_time - avg_time) < avg_time * 0.5, \
                f"Batch times vary too much, suggesting non-linear growth: {batch_times}"
    
    def test_concurrent_agent_operations(self, manager):
        """Test performance with multiple agents operating simultaneously."""
        # Create 10 agents
        agent_names = [f"Agent{i}" for i in range(10)]
        for name in agent_names:
            manager.create_agent(name)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Each agent learns and queries
        start = time.time()
        for name in agent_names:
            manager.set_agent_time(name, now)
            for i in range(10):
                manager.learn_triplet(
                    name,
                    f"fact{i}",
                    "is",
                    "true",
                    rating=Rating.Good
                )
            context = manager.get_context(name, "fact5")
            assert len(context) > 0
        total_time = time.time() - start
        
        # 10 agents × 10 triplets + 10 queries should be fast
        assert total_time < 5.0, f"Multi-agent operations took too long: {total_time}s"
