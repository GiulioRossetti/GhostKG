"""Unit tests for AgentManager."""
import pytest
from ghost_kg.manager import AgentManager
from ghost_kg.exceptions import AgentNotFoundError, ValidationError
from datetime import datetime, timezone
import tempfile
import os


class TestAgentManager:
    """Test AgentManager class."""
    
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
        """Create an AgentManager for testing."""
        return AgentManager(temp_db)
    
    def test_initialization(self, temp_db):
        """Test manager initializes correctly."""
        manager = AgentManager(temp_db)
        assert manager.db_path == temp_db
        assert manager.db is not None
        assert manager.agents == {}
    
    def test_create_agent(self, manager):
        """Test creating an agent."""
        agent = manager.create_agent("Alice")
        assert agent is not None
        assert agent.name == "Alice"
        assert "Alice" in manager.agents
    
    def test_create_duplicate_agent(self, manager):
        """Test creating an agent with existing name."""
        manager.create_agent("Alice")
        # Creating again should return existing agent
        agent2 = manager.create_agent("Alice")
        assert agent2 is not None
        assert agent2.name == "Alice"
    
    def test_get_agent(self, manager):
        """Test getting an agent."""
        manager.create_agent("Alice")
        agent = manager.get_agent("Alice")
        assert agent is not None
        assert agent.name == "Alice"
    
    def test_get_nonexistent_agent(self, manager):
        """Test getting a non-existent agent."""
        agent = manager.get_agent("NonExistent")
        assert agent is None
    
    def test_set_agent_time(self, manager):
        """Test setting agent time."""
        manager.create_agent("Alice")
        now = datetime.now(timezone.utc)
        manager.set_agent_time("Alice", now)
        
        agent = manager.get_agent("Alice")
        assert agent.current_time == now
    
    def test_set_agent_time_nonexistent(self, manager):
        """Test setting time for non-existent agent."""
        now = datetime.now(timezone.utc)
        with pytest.raises(AgentNotFoundError):
            manager.set_agent_time("NonExistent", now)
    
    def test_absorb_content(self, manager):
        """Test absorbing content."""
        manager.create_agent("Alice")
        manager.absorb_content(
            "Alice",
            "Python is awesome",
            "Bob",
            triplets=[("Python", "is", "awesome", 0.8)],
            fast_mode=True
        )
        
        # Verify it was stored (indirectly by checking no errors)
    
    def test_absorb_content_nonexistent_agent(self, manager):
        """Test absorbing content for non-existent agent."""
        with pytest.raises(AgentNotFoundError):
            manager.absorb_content("NonExistent", "content", "author")
    
    def test_absorb_content_empty(self, manager):
        """Test absorbing empty content."""
        manager.create_agent("Alice")
        with pytest.raises(ValidationError):
            manager.absorb_content("Alice", "", "author")
    
    def test_get_context(self, manager):
        """Test getting context."""
        manager.create_agent("Alice")
        manager.absorb_content(
            "Alice",
            "Python is a programming language",
            "Bob",
            triplets=[("Python", "is", "language", 0.0)],
            fast_mode=True
        )
        
        context = manager.get_context("Alice", "Python")
        assert isinstance(context, str)
    
    def test_get_context_nonexistent_agent(self, manager):
        """Test getting context for non-existent agent."""
        with pytest.raises(AgentNotFoundError):
            manager.get_context("NonExistent", "topic")
    
    def test_get_context_empty_topic(self, manager):
        """Test getting context with empty topic."""
        manager.create_agent("Alice")
        with pytest.raises(ValidationError):
            manager.get_context("Alice", "")
    
    def test_update_with_response(self, manager):
        """Test updating with response."""
        manager.create_agent("Alice")
        manager.update_with_response(
            "Alice",
            "I think Python is great",
            context="Previous discussion about Python",
            triplets=[("Python", "is", "great", 0.9)],
            fast_mode=True
        )
        
        # Verify no errors occurred
    
    def test_process_and_get_context(self, manager):
        """Test combined process and get context."""
        manager.create_agent("Alice")
        
        context = manager.process_and_get_context(
            "Alice",
            "programming",
            "Python is awesome",
            "Bob",
            triplets=[("Python", "is", "awesome", 0.8)],
            fast_mode=True
        )
        
        assert isinstance(context, str)
    
    def test_validation_agent_name(self, manager):
        """Test validation of agent name."""
        with pytest.raises(ValidationError):
            manager.create_agent("")
    
    def test_validation_content(self, manager):
        """Test validation of content."""
        manager.create_agent("Alice")
        with pytest.raises(ValidationError):
            manager.absorb_content("Alice", None, "author")
