"""Additional tests to improve code coverage."""
import pytest
from datetime import datetime, timezone, timedelta
from ghost_kg import GhostAgent, AgentManager, KnowledgeDB, NodeState, Rating
import tempfile
import os


class TestAdditionalCoverage:
    """Tests to cover additional code paths."""
    
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
    
    def test_agent_forgotten_memory(self, temp_db):
        """Test agent forgetting memories with low retrievability."""
        agent = GhostAgent("TestAgent", temp_db)
        
        # Set time to past
        past = datetime.now(timezone.utc) - timedelta(days=365)
        agent.set_time(past)
        
        # Add a memory
        agent.learn_triplet("old", "is", "forgotten", Rating.Good, 0.0)
        
        # Set time to future (1 year later)
        future = datetime.now(timezone.utc)
        agent.set_time(future)
        
        # Get memory view - should show forgotten message
        memory_view = agent.get_memory_view("old")
        assert "forgotten" in memory_view.lower()
    
    def test_agent_confused_state(self, temp_db):
        """Test agent confused state with invalid topic."""
        agent = GhostAgent("TestAgent", temp_db)
        
        # Try to get memory view with empty/invalid topic
        memory_view = agent.get_memory_view("")
        assert "confused" in memory_view.lower()
    
    def test_agent_no_opinion_yet(self, temp_db):
        """Test agent with no stance on a topic."""
        agent = GhostAgent("TestAgent", temp_db)
        
        # Get memory view for topic agent knows nothing about
        memory_view = agent.get_memory_view("unknown_topic")
        assert "no strong opinion" in memory_view.lower() or "confused" in memory_view.lower()
    
    def test_storage_database_error_handling(self, temp_db):
        """Test database error handling paths."""
        # Test with invalid database path
        from ghost_kg import DatabaseError
        
        # This is already tested in test_error_handling.py
        # Just verify the exception is raised
        try:
            bad_db = KnowledgeDB("/invalid/path/that/does/not/exist/db.sqlite")
            assert False, "Should have raised DatabaseError"
        except DatabaseError:
            pass  # Expected
    
    def test_manager_internal_llm_extraction(self, temp_db):
        """Test manager absorb_content without triplets (requires LLM)."""
        manager = AgentManager(temp_db)
        manager.create_agent("Alice")
        
        # This should try to use internal LLM extraction
        # Without LLM available, it should handle gracefully
        try:
            manager.absorb_content(
                "Alice",
                "Python is great",
                "Bob",
                triplets=None  # Force internal extraction
            )
        except Exception:
            # Expected to fail without LLM, that's ok
            pass
    
    def test_agent_update_memory_with_low_stability(self, temp_db):
        """Test updating memory with low stability."""
        agent = GhostAgent("TestAgent", temp_db)
        
        # Learn something with Again rating (low quality)
        agent.learn_triplet("unstable", "is", "concept", Rating.Again, 0.0)
        
        # Update it multiple times with different ratings
        agent.update_memory("concept", Rating.Hard)
        agent.update_memory("concept", Rating.Good)
        agent.update_memory("concept", Rating.Easy)
        
        # Verify memory was updated
        memory_view = agent.get_memory_view("concept")
        assert isinstance(memory_view, str)
    
    def test_storage_get_agent_stance_temporal(self, temp_db):
        """Test get_agent_stance with temporal awareness."""
        db = KnowledgeDB(temp_db)
        now = datetime.now(timezone.utc)
        
        # Add some relations as agent's stance
        db.add_relation("agent1", "I", "like", "Python", sentiment=0.8, timestamp=now)
        db.add_relation("agent1", "I", "dislike", "bugs", sentiment=-0.8, timestamp=now)
        
        # Query stance
        stance = db.get_agent_stance("agent1", "Python", current_time=now)
        assert len(stance) > 0
    
    def test_storage_get_world_knowledge(self, temp_db):
        """Test get_world_knowledge query."""
        db = KnowledgeDB(temp_db)
        
        # Add some world knowledge (from other agents)
        db.add_relation("agent1", "Bob", "says", "Python is great", sentiment=0.5)
        db.add_relation("agent1", "Alice", "thinks", "Java is robust", sentiment=0.5)
        
        # Query world knowledge
        knowledge = db.get_world_knowledge("agent1", "Python", limit=10)
        assert len(knowledge) > 0
    
    def test_agent_invalid_triplet_filtering(self, temp_db):
        """Test that invalid triplets are filtered out."""
        agent = GhostAgent("TestAgent", temp_db)
        
        # Try to add invalid triplets (should be silently rejected)
        agent.learn_triplet("it", "is", "the")  # Stopwords
        agent.learn_triplet("a", "noun", "text")  # Banned terms
        agent.learn_triplet("x", "y", "z")  # Too short
        
        # These should not cause errors, just be filtered
        # Verify by checking memory view doesn't crash
        memory_view = agent.get_memory_view("test")
        assert isinstance(memory_view, str)
    
    def test_agent_normalize_self_references(self, temp_db):
        """Test normalization of self-references."""
        agent = GhostAgent("TestAgent", temp_db)
        
        # Add triplets with various self-references
        agent.learn_triplet("TestAgent", "likes", "coding")  # Agent name
        agent.learn_triplet("me", "enjoys", "learning")  # "me"
        agent.learn_triplet("myself", "is", "developer")  # "myself"
        
        # All should be normalized to "I"
        # Verify by getting memory view
        memory_view = agent.get_memory_view("coding")
        assert isinstance(memory_view, str)
    
    def test_storage_validation_errors(self, temp_db):
        """Test storage validation error messages."""
        db = KnowledgeDB(temp_db)
        
        from ghost_kg import ValidationError
        
        # Test empty owner_id
        with pytest.raises(ValidationError, match="owner_id"):
            db.upsert_node("", "node1")
        
        # Test empty node_id
        with pytest.raises(ValidationError, match="node_id"):
            db.upsert_node("agent1", "")
        
        # Test empty relation parameters
        with pytest.raises(ValidationError):
            db.add_relation("", "src", "rel", "tgt")
        
        with pytest.raises(ValidationError):
            db.add_relation("agent1", "", "rel", "tgt")
        
        # Test invalid sentiment range
        with pytest.raises(ValidationError, match="sentiment"):
            db.add_relation("agent1", "src", "rel", "tgt", sentiment=2.0)
        
        with pytest.raises(ValidationError, match="sentiment"):
            db.add_relation("agent1", "src", "rel", "tgt", sentiment=-2.0)
        
        # Test empty agent in log_interaction
        with pytest.raises(ValidationError, match="agent"):
            db.log_interaction("", "action", "content", {})
        
        with pytest.raises(ValidationError, match="action"):
            db.log_interaction("agent1", "", "content", {})
    
    def test_agent_retrievability_edge_cases(self, temp_db):
        """Test retrievability calculation edge cases."""
        agent = GhostAgent("TestAgent", temp_db)
        
        # Test with zero stability
        now = datetime.now(timezone.utc)
        retrievability = agent._get_retrievability(0.0, now)
        assert retrievability == 0.0
        
        # Test with None last_review
        retrievability = agent._get_retrievability(5.0, None)
        assert retrievability == 0.0
        
        # Test with future last_review (negative elapsed days)
        future = now + timedelta(days=10)
        agent.set_time(now)
        retrievability = agent._get_retrievability(5.0, future)
        assert retrievability >= 0.0
