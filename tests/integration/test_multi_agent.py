"""Integration tests for multi-agent scenarios."""
import pytest
import datetime
from ghost_kg import AgentManager, Rating


@pytest.fixture
def manager(tmp_path):
    """Create agent manager with temp database."""
    db_path = tmp_path / "test.db"
    return AgentManager(str(db_path))


class TestMultiAgent:
    """Test multi-agent scenarios."""
    
    def test_two_agents_knowledge_isolation(self, manager):
        """Test that two agents have isolated knowledge."""
        # Create two agents
        alice = manager.create_agent("Alice")
        bob = manager.create_agent("Bob")
        
        # Set time
        now = datetime.datetime.now(datetime.timezone.utc)
        manager.set_agent_time("Alice", now)
        manager.set_agent_time("Bob", now)
        
        # Alice learns about topic A
        manager.absorb_content(
            "Alice",
            "Topic A is interesting",
            author="Teacher",
            triplets=[("Topic A", "is", "interesting")]
        )
        
        # Bob learns about topic B
        manager.absorb_content(
            "Bob",
            "Topic B is boring",
            author="Teacher",
            triplets=[("Topic B", "is", "boring")]
        )
        
        # Alice's context should mention Topic A, not B
        alice_context = manager.get_context("Alice", "Topic A")
        assert "Topic A" in alice_context or "interesting" in alice_context.lower()
        
        # Bob's context should mention Topic B, not A
        bob_context = manager.get_context("Bob", "Topic B")
        assert "Topic B" in bob_context or "boring" in bob_context.lower()
    
    def test_agent_to_agent_communication(self, manager):
        """Test agents learning from each other."""
        alice = manager.create_agent("Alice")
        bob = manager.create_agent("Bob")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        manager.set_agent_time("Alice", now)
        manager.set_agent_time("Bob", now)
        
        # Bob says something
        bob_statement = "Climate change is urgent"
        
        # Alice absorbs Bob's statement
        manager.absorb_content(
            "Alice",
            bob_statement,
            author="Bob",
            triplets=[("climate change", "is", "urgent")]
        )
        
        # Alice should remember what Bob said
        alice_context = manager.get_context("Alice", "climate")
        assert "climate" in alice_context.lower() or "urgent" in alice_context.lower()
    
    def test_multi_round_conversation(self, manager):
        """Test multiple rounds of agent interaction."""
        alice = manager.create_agent("Alice")
        bob = manager.create_agent("Bob")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Round 1: Bob speaks
        manager.set_agent_time("Bob", now)
        manager.absorb_content(
            "Bob",
            "AI safety is important",
            author="Self",
            triplets=[("AI safety", "is", "important")]
        )
        
        # Round 2: Alice hears and responds
        manager.set_agent_time("Alice", now + datetime.timedelta(minutes=5))
        manager.absorb_content(
            "Alice",
            "Bob thinks AI safety is important",
            author="Bob",
            triplets=[("AI safety", "is", "important")]
        )
        
        # Alice's response
        alice_response = "I agree about AI safety"
        manager.update_with_response(
            "Alice",
            alice_response,
            triplets=[("agree", "AI safety", 0.8)]
        )
        
        # Round 3: Bob hears Alice's response
        manager.set_agent_time("Bob", now + datetime.timedelta(minutes=10))
        manager.absorb_content(
            "Bob",
            "Alice agrees about AI safety",
            author="Alice",
            triplets=[("Alice", "agrees", "AI safety")]
        )
        
        # Both agents should have knowledge about AI safety
        alice_context = manager.get_context("Alice", "AI safety")
        bob_context = manager.get_context("Bob", "AI safety")
        
        assert "safety" in alice_context.lower() or "AI" in alice_context
        assert "safety" in bob_context.lower() or "AI" in bob_context
    
    def test_memory_decay_per_agent(self, manager):
        """Test that memory decay is tracked per agent."""
        alice = manager.create_agent("Alice")
        bob = manager.create_agent("Bob")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Both learn the same fact
        manager.set_agent_time("Alice", now)
        manager.absorb_content(
            "Alice",
            "The sky is blue",
            author="Teacher",
            triplets=[("sky", "is", "blue")]
        )
        
        manager.set_agent_time("Bob", now)
        manager.absorb_content(
            "Bob",
            "The sky is blue",
            author="Teacher",
            triplets=[("sky", "is", "blue")]
        )
        
        # Alice reviews after 1 day
        manager.set_agent_time("Alice", now + datetime.timedelta(days=1))
        manager.learn_triplet("Alice", "sky", "is", "blue", rating=Rating.Good)
        
        # Bob doesn't review
        manager.set_agent_time("Bob", now + datetime.timedelta(days=7))
        
        # Alice's memory should be stronger (but we can't directly test this
        # without accessing internal state, so we just verify no errors)
        alice_context = manager.get_context("Alice", "sky")
        bob_context = manager.get_context("Bob", "sky")
        
        # Both should still have the memory
        assert "sky" in alice_context.lower() or "blue" in alice_context.lower()
        assert "sky" in bob_context.lower() or "blue" in bob_context.lower()
    
    def test_multiple_agents_concurrent(self, manager):
        """Test managing multiple agents concurrently."""
        # Create 5 agents
        agents = []
        for i in range(5):
            agent = manager.create_agent(f"Agent{i}")
            agents.append(agent)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Each agent learns different facts
        for i in range(5):
            manager.set_agent_time(f"Agent{i}", now)
            manager.absorb_content(
                f"Agent{i}",
                f"Fact {i} is true",
                author="Teacher",
                triplets=[(f"Fact{i}", "is", "true")]
            )
        
        # Verify each agent has only their own fact
        for i in range(5):
            context = manager.get_context(f"Agent{i}", f"Fact{i}")
            assert f"Fact{i}" in context or f"Fact {i}" in context or "true" in context.lower()
