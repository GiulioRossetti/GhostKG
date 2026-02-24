"""Unit tests for AgentManager."""
import pytest
from ghost_kg import AgentManager, AgentNotFoundError, ValidationError
from ghost_kg.utils.time_utils import SimulationTime
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
        # Manager doesn't expose db_path attribute
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

    def test_set_agent_time_round_tuple(self, manager):
        """Test setting agent time using round-based tuple."""
        manager.create_agent("Alice")
        manager.set_agent_time("Alice", (2, 13))
        agent = manager.get_agent("Alice")
        assert agent.current_time.is_round_mode()
        assert agent.current_time.day == 2
        assert agent.current_time.hour == 13
    
    def test_set_agent_time_nonexistent(self, manager):
        """Test setting time for non-existent agent."""
        now = datetime.now(timezone.utc)
        with pytest.raises(AgentNotFoundError):
            manager.set_agent_time("NonExistent", now)

    def test_initialization_with_db_url(self, temp_db):
        """Test manager can initialize with explicit db_url."""
        db_url = f"sqlite:///{temp_db}"
        manager = AgentManager(db_url=db_url)
        manager.create_agent("Alice")
        assert manager.db is not None
    
    def test_absorb_content(self, manager):
        """Test absorbing content."""
        manager.create_agent("Alice")
        # Triplets should be 3-tuples (source, relation, target) without sentiment
        manager.absorb_content(
            "Alice",
            "Python is awesome",
            "Bob",
            triplets=[("Python", "is", "awesome")]
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
        # Triplets should be 3-tuples (source, relation, target) without sentiment
        manager.absorb_content(
            "Alice",
            "Python is a programming language",
            "Bob",
            triplets=[("Python", "is", "language")]
        )
        
        context = manager.get_context("Alice", "Python")
        assert isinstance(context, str)

    def test_get_context_flexible_topic_matching(self, manager, monkeypatch):
        """Test context retrieval tries token-level topic variants."""
        agent = manager.create_agent("Alice")
        seen = []

        def _fake_get_memory_view(topic):
            seen.append(topic)
            if str(topic).lower() == "ai":
                return "- AI related memory"
            return "(I have forgotten the details about topic)"

        monkeypatch.setattr(agent, "get_memory_view", _fake_get_memory_view)
        context = manager.get_context("Alice", "AI in Education")
        assert isinstance(context, str)
        assert any(str(t).lower() == "ai" for t in seen)
    
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
        # Triplets for update_with_response are (relation, target, sentiment)
        manager.update_with_response(
            "Alice",
            "I think Python is great",
            context="Previous discussion about Python",
            triplets=[("like", "Python", 0.9)]
        )
        
        # Verify no errors occurred
    
    def test_process_and_get_context(self, manager):
        """Test combined process and get context."""
        manager.create_agent("Alice")
        
        # Triplets should be 3-tuples (source, relation, target) without sentiment
        context = manager.process_and_get_context(
            "Alice",
            "programming",
            "Python is awesome",
            "Bob",
            triplets=[("Python", "is", "awesome")]
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

    def test_simulation_time_round_datetime_mapping(self):
        """Round mode should still map to datetime and datetime mode should map to round."""
        round_time = SimulationTime.from_round(3, 14)
        dt = round_time.to_datetime()
        assert dt is not None
        assert dt.tzinfo is not None

        dt_time = SimulationTime.from_datetime(datetime(2025, 1, 3, 14, 0, tzinfo=timezone.utc))
        as_round = dt_time.to_round()
        assert as_round == (3, 14)
