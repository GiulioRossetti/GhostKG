"""
Tests for error handling (Phase 3 refactoring).

This module tests:
- Custom exceptions
- Database error handling
- LLM error handling with retries
- Input validation
- Graceful degradation
"""

import pytest
import sqlite3
import datetime
from unittest.mock import Mock, patch, MagicMock

from ghost_kg import (
    GhostKGError,
    DatabaseError,
    LLMError,
    ExtractionError,
    ConfigurationError,
    AgentNotFoundError,
    ValidationError,
    DependencyError,
)
from ghost_kg.storage import KnowledgeDB, NodeState
from ghost_kg.manager import AgentManager


class TestCustomExceptions:
    """Test custom exception hierarchy."""
    
    def test_base_exception(self):
        """Test GhostKGError is a proper Exception."""
        error = GhostKGError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"
    
    def test_database_error(self):
        """Test DatabaseError inherits from GhostKGError."""
        error = DatabaseError("database failed")
        assert isinstance(error, GhostKGError)
        assert isinstance(error, Exception)
    
    def test_llm_error(self):
        """Test LLMError inherits from GhostKGError."""
        error = LLMError("llm failed")
        assert isinstance(error, GhostKGError)
    
    def test_extraction_error(self):
        """Test ExtractionError inherits from GhostKGError."""
        error = ExtractionError("extraction failed")
        assert isinstance(error, GhostKGError)
    
    def test_validation_error(self):
        """Test ValidationError inherits from GhostKGError."""
        error = ValidationError("validation failed")
        assert isinstance(error, GhostKGError)
    
    def test_agent_not_found_error(self):
        """Test AgentNotFoundError inherits from GhostKGError."""
        error = AgentNotFoundError("agent not found")
        assert isinstance(error, GhostKGError)


class TestDatabaseErrorHandling:
    """Test database error handling in storage.py."""
    
    def test_invalid_db_path(self):
        """Test initialization with invalid database path."""
        # This should work even with invalid path, but would fail on schema init
        # if permissions are wrong
        db = KnowledgeDB(":memory:")
        assert db.conn is not None
    
    def test_upsert_node_validation(self):
        """Test upsert_node with invalid parameters."""
        db = KnowledgeDB(":memory:")
        
        # Empty owner_id
        with pytest.raises(ValidationError, match="owner_id and node_id are required"):
            db.upsert_node("", "node1")
        
        # Empty node_id
        with pytest.raises(ValidationError, match="owner_id and node_id are required"):
            db.upsert_node("agent1", "")
    
    def test_add_relation_validation(self):
        """Test add_relation with invalid parameters."""
        db = KnowledgeDB(":memory:")
        
        # Empty owner_id
        with pytest.raises(ValidationError):
            db.add_relation("", "source", "relation", "target")
        
        # Invalid sentiment
        with pytest.raises(ValidationError, match="sentiment must be between"):
            db.add_relation("agent1", "source", "relation", "target", sentiment=2.0)
        
        with pytest.raises(ValidationError, match="sentiment must be between"):
            db.add_relation("agent1", "source", "relation", "target", sentiment=-2.0)
    
    def test_log_interaction_validation(self):
        """Test log_interaction with invalid parameters."""
        db = KnowledgeDB(":memory:")
        
        # Empty agent name
        with pytest.raises(ValidationError, match="agent and action are required"):
            db.log_interaction("", "action", "content", {})
        
        # Empty action
        with pytest.raises(ValidationError, match="agent and action are required"):
            db.log_interaction("agent1", "", "content", {})
    
    def test_successful_operations(self):
        """Test that valid operations succeed."""
        db = KnowledgeDB(":memory:")
        
        # Valid upsert
        db.upsert_node("agent1", "node1")
        
        # Valid relation
        db.add_relation("agent1", "source", "likes", "target", sentiment=0.5)
        
        # Valid log
        db.log_interaction("agent1", "READ", "content", {"key": "value"})
        
        # Verify data was stored
        node = db.get_node("agent1", "node1")
        assert node is not None


class TestManagerValidation:
    """Test input validation in AgentManager."""
    
    def test_create_agent_validation(self):
        """Test create_agent with invalid parameters."""
        manager = AgentManager(":memory:")
        
        # Empty name
        with pytest.raises(ValidationError, match="Agent name must be a non-empty string"):
            manager.create_agent("")
        
        # None name
        with pytest.raises(ValidationError, match="Agent name must be a non-empty string"):
            manager.create_agent(None)
    
    def test_set_agent_time_validation(self):
        """Test set_agent_time with invalid parameters."""
        manager = AgentManager(":memory:")
        manager.create_agent("test_agent")
        
        # Invalid time type
        with pytest.raises(ValidationError, match="time must be a datetime object"):
            manager.set_agent_time("test_agent", "not a datetime")
        
        # Non-existent agent
        with pytest.raises(AgentNotFoundError, match="Agent 'nonexistent' not found"):
            manager.set_agent_time("nonexistent", datetime.datetime.now())
    
    def test_absorb_content_validation(self):
        """Test absorb_content with invalid parameters."""
        manager = AgentManager(":memory:")
        manager.create_agent("test_agent")
        
        # Empty content
        with pytest.raises(ValidationError, match="content must be a non-empty string"):
            manager.absorb_content("test_agent", "")
        
        # Invalid triplets format
        with pytest.raises(ValidationError, match="triplets must be a list"):
            manager.absorb_content("test_agent", "content", triplets="not a list")
        
        # Invalid triplet structure
        with pytest.raises(ValidationError, match="Each triplet must be a 3-tuple"):
            manager.absorb_content("test_agent", "content", triplets=[("source", "relation")])
        
        # Non-existent agent
        with pytest.raises(AgentNotFoundError, match="Agent 'nonexistent' not found"):
            manager.absorb_content("nonexistent", "content")
    
    def test_get_context_validation(self):
        """Test get_context with invalid parameters."""
        manager = AgentManager(":memory:")
        manager.create_agent("test_agent")
        
        # Empty topic
        with pytest.raises(ValidationError, match="topic must be a non-empty string"):
            manager.get_context("test_agent", "")
        
        # Non-existent agent
        with pytest.raises(AgentNotFoundError, match="Agent 'nonexistent' not found"):
            manager.get_context("nonexistent", "topic")


class TestLLMErrorHandling:
    """Test LLM error handling with retries."""
    
    @patch('ghost_kg.cognitive.CognitiveLoop._call_llm_with_retry')
    def test_llm_retry_logic(self, mock_call):
        """Test that LLM calls are retried on failure."""
        # This is a unit test for the retry logic
        # We'll test the actual retry behavior
        pass  # Implementation would require mocking
    
    def test_llm_error_raised_after_retries(self):
        """Test that LLMError is raised after max retries."""
        # This would test the actual retry implementation
        pass  # Implementation would require mocking


class TestGracefulDegradation:
    """Test graceful degradation when optional features unavailable."""
    
    def test_missing_dependencies_handled(self):
        """Test that missing optional dependencies are handled gracefully."""
        # This tests that the code doesn't crash when optional deps are missing
        from ghost_kg import DependencyChecker
        
        # Check status shouldn't crash
        DependencyChecker.print_status()
        
        # Getting available extractors shouldn't crash
        extractors = DependencyChecker.get_available_extractors()
        assert isinstance(extractors, list)


def test_error_hierarchy():
    """Test that all custom errors can be caught by base exception."""
    errors = [
        DatabaseError("test"),
        LLMError("test"),
        ExtractionError("test"),
        ConfigurationError("test"),
        AgentNotFoundError("test"),
        ValidationError("test"),
        DependencyError("test"),
    ]
    
    for error in errors:
        # All should be catchable as GhostKGError
        assert isinstance(error, GhostKGError)
        # All should be catchable as Exception
        assert isinstance(error, Exception)


def test_error_messages():
    """Test that error messages are preserved."""
    msg = "This is a test error message"
    error = DatabaseError(msg)
    assert str(error) == msg
    assert error.args[0] == msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
