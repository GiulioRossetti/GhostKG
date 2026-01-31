"""Unit tests for KnowledgeDB storage layer."""
import pytest
from datetime import datetime, timezone, timedelta
from ghost_kg import KnowledgeDB, NodeState, DatabaseError, ValidationError
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
        # Database doesn't expose db_path attribute, just conn
        assert db.conn is not None
    
    def test_upsert_node(self, db):
        """Test upserting a node."""
        now = datetime.now(timezone.utc)
        fsrs_state = NodeState(
            stability=5.0,
            difficulty=5.0,
            last_review=now,
            reps=1,
            state=2
        )
        db.upsert_node(
            owner_id="agent1",
            node_id="concept1",
            fsrs_state=fsrs_state,
            timestamp=now
        )
        
        # Verify node was inserted
        node = db.get_node("agent1", "concept1")
        assert node is not None
        assert node["stability"] == 5.0
    
    def test_upsert_node_update(self, db):
        """Test updating an existing node."""
        now = datetime.now(timezone.utc)
        
        # Insert initial
        fsrs_state1 = NodeState(5.0, 5.0, now, 1, 2)
        db.upsert_node("agent1", "concept1", fsrs_state1, now)
        
        # Update
        fsrs_state2 = NodeState(7.0, 4.0, now, 2, 2)
        db.upsert_node("agent1", "concept1", fsrs_state2, now)
        
        # Verify update
        node = db.get_node("agent1", "concept1")
        assert node["stability"] == 7.0
        assert node["reps"] == 2
    
    def test_get_node_not_found(self, db):
        """Test getting a non-existent node."""
        node = db.get_node("agent1", "nonexistent")
        assert node is None
    
    def test_delete_node(self, db):
        """Test deleting a node (via SQL)."""
        now = datetime.now(timezone.utc)
        fsrs_state = NodeState(5.0, 5.0, now, 1, 2)
        db.upsert_node("agent1", "concept1", fsrs_state, now)
        
        # Verify it exists
        assert db.get_node("agent1", "concept1") is not None
        
        # Delete using SQL directly (no delete_node method in API)
        db.conn.execute("DELETE FROM nodes WHERE owner_id = ? AND id = ?", 
                       ("agent1", "concept1"))
        db.conn.commit()
        
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
        
        # Verify relation was added by querying edges table directly
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM edges 
            WHERE owner_id = ? AND source = ?
        """, ("agent1", "Python"))
        relations = cursor.fetchall()
        assert len(relations) > 0
    
    def test_get_relations_empty(self, db):
        """Test getting relations for non-existent source."""
        # Query edges table directly (no get_relations method in API)
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM edges 
            WHERE owner_id = ? AND source = ?
        """, ("agent1", "nonexistent"))
        relations = cursor.fetchall()
        assert len(relations) == 0
    
    def test_temporal_query(self, db):
        """Test querying by time."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=7)
        
        # Add nodes at different times
        fsrs_state1 = NodeState(5.0, 5.0, now, 1, 2)
        fsrs_state2 = NodeState(5.0, 5.0, past, 1, 2)
        db.upsert_node("agent1", "recent", fsrs_state1, now)
        db.upsert_node("agent1", "old", fsrs_state2, past)
        
        # Query recent (last 3 days) using SQL directly (no query_temporal in API)
        cursor = db.conn.cursor()
        since = now - timedelta(days=3)
        cursor.execute("""
            SELECT id FROM nodes 
            WHERE owner_id = ? AND created_at >= ?
            LIMIT 10
        """, ("agent1", since))
        recent = cursor.fetchall()
        
        # Should find recent node
        recent_ids = [r["id"] for r in recent]
        assert "recent" in recent_ids
        assert "old" not in recent_ids
    
    def test_query_by_sentiment(self, db):
        """Test querying by sentiment."""
        # Add relations with different sentiments
        db.add_relation("agent1", "good", "is", "positive", sentiment=0.8)
        db.add_relation("agent1", "bad", "is", "negative", sentiment=-0.8)
        
        # Query positive using SQL directly (no query_by_sentiment in API)
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM edges 
            WHERE owner_id = ? AND sentiment >= ?
        """, ("agent1", 0.5))
        positive = cursor.fetchall()
        assert len(positive) > 0
        
        # Query negative
        cursor.execute("""
            SELECT * FROM edges 
            WHERE owner_id = ? AND sentiment <= ?
        """, ("agent1", -0.5))
        negative = cursor.fetchall()
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
        fsrs_state = NodeState(5.0, 5.0, now, 1, 2)
        with pytest.raises(ValidationError):
            db.upsert_node("", "node1", fsrs_state, now)
    
    def test_validation_empty_node_id(self, db):
        """Test validation catches empty node_id."""
        now = datetime.now(timezone.utc)
        fsrs_state = NodeState(5.0, 5.0, now, 1, 2)
        with pytest.raises(ValidationError):
            db.upsert_node("agent1", "", fsrs_state, now)
    
    def test_validation_sentiment_range(self, db):
        """Test validation catches invalid sentiment."""
        with pytest.raises(ValidationError):
            db.add_relation("agent1", "a", "b", "c", sentiment=2.0)  # >1.0
        
        with pytest.raises(ValidationError):
            db.add_relation("agent1", "a", "b", "c", sentiment=-2.0)  # <-1.0
    
    def test_add_relation_none_sentiment(self, db):
        """Test that None sentiment is handled gracefully by using default value."""
        # Should not raise an error, should use default 0.0
        db.add_relation("agent1", "a", "relation", "b", sentiment=None)
        
        # Verify relation was added
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT sentiment FROM edges 
            WHERE owner_id = ? AND source = ? AND target = ?
        """, ("agent1", "a", "b"))
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 0.0  # Default sentiment
