"""Unit tests for GhostAgent."""
import pytest
from datetime import datetime, timezone, timedelta
from ghost_kg.agent import GhostAgent
from ghost_kg.storage import KnowledgeDB
from ghost_kg.fsrs import Rating
import tempfile
import os


class TestGhostAgent:
    """Test GhostAgent class."""
    
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
    def agent(self, temp_db):
        """Create a GhostAgent for testing."""
        return GhostAgent("TestAgent", temp_db)
    
    def test_initialization(self, temp_db):
        """Test agent initializes correctly."""
        agent = GhostAgent("TestAgent", temp_db)
        assert agent.name == "TestAgent"
        assert agent.db is not None
        assert agent.fsrs is not None
        assert agent.current_time is not None
    
    def test_learn_triplet(self, agent):
        """Test learning a triplet."""
        agent.learn_triplet("Python", "is", "awesome", Rating.Good, 0.8)
        
        # Query to verify it was stored
        memories = agent.query_memories("Python", limit=10)
        assert len(memories) > 0
    
    def test_query_memories_by_topic(self, agent):
        """Test querying memories by topic."""
        # Add some memories
        agent.learn_triplet("Python", "is", "language", Rating.Good, 0.0)
        agent.learn_triplet("Java", "is", "language", Rating.Good, 0.0)
        agent.learn_triplet("Python", "has", "simplicity", Rating.Good, 0.5)
        
        # Query for Python
        results = agent.query_memories("Python", limit=10)
        assert len(results) > 0
        # Should contain Python-related memories
        python_found = any("Python" in str(r) for r in results)
        assert python_found
    
    def test_query_recent_memories(self, agent):
        """Test querying recent memories."""
        now = datetime.now(timezone.utc)
        agent.set_time(now)
        
        # Add a memory
        agent.learn_triplet("topic", "is", "current", Rating.Good, 0.0)
        
        # Query recent
        recent = agent.get_recent_memories(days=1, limit=10)
        assert len(recent) > 0
    
    def test_set_time(self, agent):
        """Test setting agent time."""
        now = datetime.now(timezone.utc)
        agent.set_time(now)
        assert agent.current_time == now
        
        # Set future time
        future = now + timedelta(days=7)
        agent.set_time(future)
        assert agent.current_time == future
    
    def test_query_by_sentiment(self, agent):
        """Test querying by sentiment."""
        # Add memories with different sentiments
        agent.learn_triplet("good", "is", "positive", Rating.Good, 0.8)
        agent.learn_triplet("bad", "is", "negative", Rating.Good, -0.8)
        agent.learn_triplet("neutral", "is", "okay", Rating.Good, 0.0)
        
        # Query positive memories
        positive = agent.query_by_sentiment(min_sentiment=0.5, limit=10)
        assert len(positive) > 0
        
        # Query negative memories
        negative = agent.query_by_sentiment(max_sentiment=-0.5, limit=10)
        assert len(negative) > 0
