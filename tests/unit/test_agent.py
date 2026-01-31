"""Unit tests for GhostAgent."""
import pytest
from datetime import datetime, timezone, timedelta
from ghost_kg import GhostAgent, KnowledgeDB, Rating
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
        
        # Verify it was stored by getting memory view
        memory_view = agent.get_memory_view("Python")
        assert memory_view is not None
        assert len(memory_view) > 0
    
    def test_learn_triplet_none_sentiment(self, agent):
        """Test that None sentiment is handled gracefully."""
        # Should not raise an error, should use default 0.0
        agent.learn_triplet("Python", "is", "great", Rating.Good, sentiment=None)
        
        # Verify it was stored
        memory_view = agent.get_memory_view("Python")
        assert memory_view is not None
        assert len(memory_view) > 0
    
    def test_query_memories_by_topic(self, agent):
        """Test querying memories by topic."""
        # Add some memories
        agent.learn_triplet("Python", "is", "language", Rating.Good, 0.0)
        agent.learn_triplet("Java", "is", "language", Rating.Good, 0.0)
        agent.learn_triplet("Python", "has", "simplicity", Rating.Good, 0.5)
        
        # Get memory view for Python
        memory_view = agent.get_memory_view("Python")
        assert memory_view is not None
        assert len(memory_view) > 0
        # Memory view should be a string
        assert isinstance(memory_view, str)
    
    def test_query_recent_memories(self, agent):
        """Test querying recent memories via SQL."""
        now = datetime.now(timezone.utc)
        agent.set_time(now)
        
        # Add a memory
        agent.learn_triplet("topic", "is", "current", Rating.Good, 0.0)
        
        # Query recent using SQL directly (no get_recent_memories in API)
        cursor = agent.db.conn.cursor()
        since = now - timedelta(days=1)
        cursor.execute("""
            SELECT * FROM edges 
            WHERE owner_id = ? AND created_at >= ?
            ORDER BY created_at DESC
        """, (agent.name, since))
        recent = cursor.fetchall()
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
        """Test querying by sentiment via SQL."""
        # Add memories with different sentiments
        agent.learn_triplet("good", "is", "positive", Rating.Good, 0.8)
        agent.learn_triplet("bad", "is", "negative", Rating.Good, -0.8)
        agent.learn_triplet("neutral", "is", "okay", Rating.Good, 0.0)
        
        # Query positive memories using SQL directly (no query_by_sentiment in API)
        cursor = agent.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM edges 
            WHERE owner_id = ? AND sentiment >= ?
        """, (agent.name, 0.5))
        positive = cursor.fetchall()
        assert len(positive) > 0
        
        # Query negative memories
        cursor.execute("""
            SELECT * FROM edges 
            WHERE owner_id = ? AND sentiment <= ?
        """, (agent.name, -0.5))
        negative = cursor.fetchall()
        assert len(negative) > 0
