"""Unit tests for KnowledgeDB storage layer."""
import pytest
from datetime import datetime, timezone, timedelta
from ghost_kg.storage import KnowledgeDB
from ghost_kg.exceptions import DatabaseError, ValidationError
import tempfile
import os


class TestKnowledgeDB:
    """Test KnowledgeDB class."""
    
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
    def db(self, temp_db):
        """Create a KnowledgeDB for testing."""
        return KnowledgeDB(temp_db)
    
    def test_initialization(self, temp_db):
        """Test database initializes correctly."""
        db = KnowledgeDB(temp_db)
        assert db.db_path == temp_db
        assert db.conn is not None
    
    def test_upsert_node(self, db):
        """Test upserting a node."""
        now = datetime.now(timezone.utc)
        db.upsert_node(
            owner_id="agent1",
            node_id="concept1",
            stability=5.0,
            difficulty=5.0,
            last_review=now,
            reps=1,
            state=2
        )
        
        # Verify node was inserted
        node = db.get_node("agent1", "concept1")
        assert node is not None
        assert node["stability"] == 5.0
    
    def test_upsert_node_update(self, db):
        """Test updating an existing node."""
        now = datetime.now(timezone.utc)
        
        # Insert initial
        db.upsert_node("agent1", "concept1", 5.0, 5.0, now, 1, 2)
        
        # Update
        db.upsert_node("agent1", "concept1", 7.0, 4.0, now, 2, 2)
        
        # Verify update
        node = db.get_node("agent1", "concept1")
        assert node["stability"] == 7.0
        assert node["reps"] == 2
    
    def test_get_node_not_found(self, db):
        """Test getting a non-existent node."""
        node = db.get_node("agent1", "nonexistent")
        assert node is None
    
    def test_delete_node(self, db):
        """Test deleting a node."""
        now = datetime.now(timezone.utc)
        db.upsert_node("agent1", "concept1", 5.0, 5.0, now, 1, 2)
        
        # Verify it exists
        assert db.get_node("agent1", "concept1") is not None
        
        # Delete
        db.delete_node("agent1", "concept1")
        
        # Verify it's gone
        assert db.get_node("agent1", "concept1") is None
    
    def test_add_relation(self, db):
        """Test adding a relation."""
        db.add_relation(
            owner_id="agent1",
            source="Python",
            relation="is",
            target="language",
            sentiment=0.0
        )
        
        # Verify relation was added
        relations = db.get_relations("agent1", "Python")
        assert len(relations) > 0
    
    def test_get_relations_empty(self, db):
        """Test getting relations for non-existent source."""
        relations = db.get_relations("agent1", "nonexistent")
        assert len(relations) == 0
    
    def test_temporal_query(self, db):
        """Test querying by time."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=7)
        
        # Add nodes at different times
        db.upsert_node("agent1", "recent", 5.0, 5.0, now, 1, 2)
        db.upsert_node("agent1", "old", 5.0, 5.0, past, 1, 2)
        
        # Query recent (last 3 days)
        recent = db.query_temporal(
            owner_id="agent1",
            since=now - timedelta(days=3),
            limit=10
        )
        
        # Should find recent node
        recent_ids = [r["node_id"] for r in recent]
        assert "recent" in recent_ids
        assert "old" not in recent_ids
    
    def test_query_by_sentiment(self, db):
        """Test querying by sentiment."""
        # Add relations with different sentiments
        db.add_relation("agent1", "good", "is", "positive", sentiment=0.8)
        db.add_relation("agent1", "bad", "is", "negative", sentiment=-0.8)
        
        # Query positive
        positive = db.query_by_sentiment("agent1", min_sentiment=0.5)
        assert len(positive) > 0
        
        # Query negative
        negative = db.query_by_sentiment("agent1", max_sentiment=-0.5)
        assert len(negative) > 0
    
    def test_log_interaction(self, db):
        """Test logging an interaction."""
        now = datetime.now(timezone.utc)
        db.log_interaction(
            agent="agent1",
            action="READ",
            content="test content",
            annotations={"key": "value"},
            timestamp=now
        )
        
        # Logs don't have a direct query method, but we can verify no errors
        # occurred during logging
    
    def test_validation_empty_owner_id(self, db):
        """Test validation catches empty owner_id."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            db.upsert_node("", "node1", 5.0, 5.0, now, 1, 2)
    
    def test_validation_empty_node_id(self, db):
        """Test validation catches empty node_id."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            db.upsert_node("agent1", "", 5.0, 5.0, now, 1, 2)
    
    def test_validation_sentiment_range(self, db):
        """Test validation catches invalid sentiment."""
        with pytest.raises(ValidationError):
            db.add_relation("agent1", "a", "b", "c", sentiment=2.0)  # >1.0
        
        with pytest.raises(ValidationError):
            db.add_relation("agent1", "a", "b", "c", sentiment=-2.0)  # <-1.0
