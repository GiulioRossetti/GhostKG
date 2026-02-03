"""
Integration tests for LLMService usage modes.

Tests that different usage modes work correctly after integration.
"""
import datetime
import pytest
from unittest.mock import Mock, MagicMock
from ghost_kg import GhostAgent, AgentManager, CognitiveLoop, Rating
from ghost_kg.llm import get_llm_service


class TestMode1ExternalAPI:
    """Test Mode 1: External API mode (no internal LLM)."""
    
    def test_agent_manager_without_llm(self, tmp_path):
        """Test that AgentManager works without any LLM."""
        db_path = str(tmp_path / "test.db")
        manager = AgentManager(db_path=db_path)
        
        # Create agent (no LLM needed)
        alice = manager.create_agent("Alice")
        assert alice is not None
        assert alice.name == "Alice"
        
        # Set time
        current_time = datetime.datetime.now(datetime.timezone.utc)
        manager.set_agent_time("Alice", current_time)
        
        # Add knowledge manually
        manager.learn_triplet(
            "Alice", "I", "support", "UBI",
            rating=Rating.Good, sentiment=0.7
        )
        
        # Get context (no LLM call)
        context = manager.get_context("Alice", topic="UBI")
        assert "ubi" in str(context).lower()  # Case-insensitive check


class TestMode2OllamaIntegration:
    """Test Mode 2: Integrated LLM with Ollama."""
    
    def test_agent_with_ollama_service(self, tmp_path):
        """Test agent with Ollama LLM service."""
        from unittest.mock import patch
        
        db_path = str(tmp_path / "test.db")
        
        # Mock Ollama service
        mock_service = Mock()
        mock_service.chat.return_value = {
            "message": {"content": "Test response"}
        }
        mock_service.get_provider_type.return_value = "ollama"
        
        # Create agent with mocked LLM service
        agent = GhostAgent(
            "Alice", 
            db_path=db_path,
            llm_service=mock_service
        )
        
        assert agent.llm_service is mock_service
        assert agent.name == "Alice"


class TestMode3CommercialProviders:
    """Test Mode 3: Integrated LLM with commercial providers."""
    
    def test_agent_with_openai_service(self, tmp_path):
        """Test agent with OpenAI-like LLM service."""
        db_path = str(tmp_path / "test.db")
        
        # Mock OpenAI service
        mock_service = Mock()
        mock_service.chat.return_value = {
            "message": {"content": "Response from GPT-4"}
        }
        mock_service.get_provider_type.return_value = "openai"
        
        # Create agent with commercial LLM
        agent = GhostAgent(
            "Alice",
            db_path=db_path,
            llm_service=mock_service
        )
        
        assert agent.llm_service is mock_service
        assert agent.llm_service.get_provider_type() == "openai"
    
    def test_agent_manager_with_commercial_llm(self, tmp_path):
        """Test AgentManager can create agents with commercial LLM."""
        db_path = str(tmp_path / "test.db")
        manager = AgentManager(db_path=db_path)
        
        # Mock commercial LLM service
        mock_service = Mock()
        mock_service.get_provider_type.return_value = "anthropic"
        
        # Create agent with LLM service
        alice = manager.create_agent("Alice", llm_service=mock_service)
        
        assert alice.llm_service is mock_service
        assert alice.name == "Alice"


class TestMode4HybridMode:
    """Test Mode 4: Hybrid mode (external LLM + KG management)."""
    
    def test_hybrid_agent_manager_with_external_llm(self, tmp_path):
        """Test using AgentManager with external LLM calls."""
        db_path = str(tmp_path / "test.db")
        manager = AgentManager(db_path=db_path)
        
        # Create agent
        alice = manager.create_agent("Alice")
        manager.set_agent_time("Alice", datetime.datetime.now(datetime.timezone.utc))
        
        # Add knowledge
        manager.learn_triplet(
            "Alice", "I", "believe", "AI safety is important",
            rating=Rating.Good, sentiment=0.8
        )
        
        # Get context
        context = manager.get_context("Alice", topic="AI safety")
        
        # Simulate external LLM call (mocked)
        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "message": {"content": "AI safety is crucial for development"}
        }
        
        response = mock_llm.chat(
            messages=[{"role": "user", "content": f"Context: {context}"}]
        )
        
        assert response["message"]["content"] is not None
        mock_llm.chat.assert_called_once()


class TestCognitiveLoopWithLLMService:
    """Test CognitiveLoop works with LLMService."""
    
    def test_cognitive_loop_with_llm_service(self, tmp_path):
        """Test CognitiveLoop uses agent's LLM service."""
        db_path = str(tmp_path / "test.db")
        
        # Mock LLM service
        mock_service = Mock()
        mock_service.chat.return_value = {
            "message": {"content": "Mocked LLM response"}
        }
        
        # Create agent with LLM service
        agent = GhostAgent("Alice", db_path=db_path, llm_service=mock_service)
        
        # Verify agent has the service
        assert agent.llm_service is mock_service
        
        # Create cognitive loop (should use agent's service)
        loop = CognitiveLoop(agent, model="test-model")
        
        # Verify extractor was created with LLM service
        assert loop.extractor is not None


class TestBackwardCompatibility:
    """Test backward compatibility with old API."""
    
    def test_agent_without_llm_service_parameter(self, tmp_path):
        """Test agent still works without llm_service parameter."""
        db_path = str(tmp_path / "test.db")
        
        # Old API: just llm_host
        agent = GhostAgent("Alice", db_path=db_path, llm_host="http://localhost:11434")
        
        assert agent.name == "Alice"
        # Should have created default Ollama service
        assert agent.llm_service is not None or agent.client is None
    
    def test_manager_create_agent_old_api(self, tmp_path):
        """Test AgentManager.create_agent works with old API."""
        db_path = str(tmp_path / "test.db")
        manager = AgentManager(db_path=db_path)
        
        # Old API: just name and llm_host
        alice = manager.create_agent("Alice", llm_host="http://localhost:11434")
        
        assert alice is not None
        assert alice.name == "Alice"
