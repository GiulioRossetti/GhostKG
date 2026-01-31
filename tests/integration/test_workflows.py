"""Integration tests for complete workflows."""
import pytest
from ghost_kg import AgentManager
from datetime import datetime, timezone, timedelta
import tempfile
import os


class TestWorkflows:
    """Test complete workflows."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except:
            pass
    
    @pytest.fixture
    def manager(self, temp_db):
        """Create agent manager with temp database."""
        return AgentManager(temp_db)
    
    def test_simple_conversation(self, manager):
        """Test simple two-agent conversation."""
        # Create agents
        alice = manager.create_agent("Alice")
        bob = manager.create_agent("Bob")
        
        assert alice is not None
        assert bob is not None
        
        # Alice learns about climate
        manager.absorb_content(
            "Alice",
            "Climate change is urgent",
            author="Bob",
            triplets=[("climate change", "is", "urgent")]
        )
        
        # Get context for Alice
        context = manager.get_context("Alice", "climate")
        
        # Verify context contains learned info
        assert isinstance(context, str)
        assert len(context) > 0
    
    def test_multi_round_interaction(self, manager):
        """Test multi-round interaction between agents."""
        # Create agents
        manager.create_agent("Alice")
        manager.create_agent("Bob")
        
        # Set initial time
        now = datetime.now(timezone.utc)
        manager.set_agent_time("Alice", now)
        manager.set_agent_time("Bob", now)
        
        # Round 1: Bob tells Alice about Python
        manager.absorb_content(
            "Alice",
            "Python is a great programming language",
            "Bob",
            triplets=[("Python", "is", "language")]
        )
        
        # Round 2: Later, Alice recalls and responds
        future = now + timedelta(hours=1)
        manager.set_agent_time("Alice", future)
        
        context = manager.get_context("Alice", "Python")
        assert isinstance(context, str)
        
        # Alice generates response and updates her knowledge
        # update_with_response uses (relation, target, sentiment) format
        manager.update_with_response(
            "Alice",
            "Yes, Python is very popular",
            context=context,
            triplets=[("like", "Python", 0.7)]
        )
    
    def test_process_and_get_context_workflow(self, manager):
        """Test the combined process_and_get_context workflow."""
        manager.create_agent("Alice")
        
        # Set time
        now = datetime.now(timezone.utc)
        manager.set_agent_time("Alice", now)
        
        # Alice receives and processes content, getting context in one step
        context = manager.process_and_get_context(
            agent_name="Alice",
            topic="AI",
            text="Artificial Intelligence is transforming the world",
            author="Bob",
            triplets=[("AI", "is transforming", "world")]
        )
        
        assert isinstance(context, str)
        assert len(context) > 0
    
    def test_knowledge_persistence(self, temp_db):
        """Test that knowledge persists across manager instances."""
        # Create first manager and add knowledge
        manager1 = AgentManager(temp_db)
        manager1.create_agent("Alice")
        manager1.absorb_content(
            "Alice",
            "Python is awesome",
            "Bob",
            triplets=[("Python", "is", "awesome")]
        )
        
        # Create second manager with same database
        manager2 = AgentManager(temp_db)
        manager2.create_agent("Alice")  # Re-create agent to load existing data
        
        # Verify knowledge is available
        context = manager2.get_context("Alice", "Python")
        assert isinstance(context, str)
    
    def test_multi_agent_scenario(self, manager):
        """Test scenario with multiple agents."""
        # Create multiple agents
        agents = ["Alice", "Bob", "Charlie"]
        for name in agents:
            manager.create_agent(name)
        
        # Each agent learns something
        now = datetime.now(timezone.utc)
        manager.set_agent_time("Alice", now)
        manager.set_agent_time("Bob", now)
        manager.set_agent_time("Charlie", now)
        
        # Alice learns about Python
        manager.absorb_content(
            "Alice",
            "Python is versatile",
            "Bob",
            triplets=[("Python", "is", "versatile")]
        )
        
        # Bob learns about Java
        manager.absorb_content(
            "Bob",
            "Java is robust",
            "Charlie",
            triplets=[("Java", "is", "robust")]
        )
        
        # Charlie learns about JavaScript
        manager.absorb_content(
            "Charlie",
            "JavaScript runs everywhere",
            "Alice",
            triplets=[("JavaScript", "runs in", "browsers")]
        )
        
        # Verify each agent has their own knowledge
        alice_context = manager.get_context("Alice", "Python")
        bob_context = manager.get_context("Bob", "Java")
        charlie_context = manager.get_context("Charlie", "JavaScript")
        
        assert isinstance(alice_context, str)
        assert isinstance(bob_context, str)
        assert isinstance(charlie_context, str)
