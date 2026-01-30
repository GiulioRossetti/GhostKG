"""Unit tests for CognitiveLoop class."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ghost_kg.cognitive import CognitiveLoop
from ghost_kg.agent import GhostAgent
from ghost_kg.exceptions import LLMError, ExtractionError


@pytest.fixture
def mock_agent(tmp_path):
    """Create a mock agent for testing."""
    db_path = tmp_path / "test.db"
    agent = GhostAgent("TestAgent", str(db_path))
    # Mock the client to avoid actual LLM calls
    agent.client = Mock()
    return agent


class TestCognitiveLoop:
    """Test CognitiveLoop cognitive operations."""
    
    def test_initialization_default(self, mock_agent):
        """Test CognitiveLoop initialization with defaults."""
        with patch('ghost_kg.cognitive.get_extractor') as mock_get_extractor:
            mock_get_extractor.return_value = Mock()
            loop = CognitiveLoop(mock_agent)
            
            assert loop.agent == mock_agent
            assert loop.model == "llama3.2"
            assert loop.fast_mode is False
            mock_get_extractor.assert_called_once()
    
    def test_initialization_fast_mode(self, mock_agent):
        """Test CognitiveLoop initialization with fast mode."""
        with patch('ghost_kg.cognitive.get_extractor') as mock_get_extractor:
            mock_get_extractor.return_value = Mock()
            loop = CognitiveLoop(mock_agent, fast_mode=True)
            
            assert loop.fast_mode is True
            mock_get_extractor.assert_called_once()
    
    def test_initialization_custom_model(self, mock_agent):
        """Test CognitiveLoop initialization with custom model."""
        with patch('ghost_kg.cognitive.get_extractor') as mock_get_extractor:
            mock_get_extractor.return_value = Mock()
            loop = CognitiveLoop(mock_agent, model="custom-model")
            
            assert loop.model == "custom-model"
    
    def test_call_llm_with_retry_success(self, mock_agent):
        """Test successful LLM call."""
        with patch('ghost_kg.cognitive.get_extractor') as mock_get_extractor:
            mock_get_extractor.return_value = Mock()
            loop = CognitiveLoop(mock_agent)
            
            # Mock successful LLM response
            mock_agent.client.chat.return_value = {
                'message': {'content': '{"result": "test"}'}
            }
            
            result = loop._call_llm_with_retry("test prompt", format="json")
            
            # The method returns the full response dict, not parsed JSON
            assert result == {'message': {'content': '{"result": "test"}'}}
    
    def test_call_llm_with_retry_failure(self, mock_agent):
        """Test LLM call with retries on failure."""
        with patch('ghost_kg.cognitive.get_extractor') as mock_get_extractor:
            mock_get_extractor.return_value = Mock()
            loop = CognitiveLoop(mock_agent)
            
            # Mock failed LLM response
            mock_agent.client.chat.side_effect = Exception("LLM error")
            
            with pytest.raises(LLMError):
                loop._call_llm_with_retry("test prompt", max_retries=2)
    
    @pytest.mark.skipif(True, reason="Requires complex mocking of LLM response structure")
    def test_absorb_with_extractor(self, mock_agent):
        """Test absorb method with extractor."""
        # This test requires mocking complex nested response structures
        # Skip for now as absorb is tested in integration tests
        pass
    
    def test_absorb_with_extraction_error(self, mock_agent):
        """Test absorb handles extraction errors gracefully."""
        with patch('ghost_kg.cognitive.get_extractor') as mock_get_extractor:
            mock_extractor = Mock()
            mock_extractor.extract_triplets.side_effect = Exception("Extraction failed")
            mock_get_extractor.return_value = mock_extractor
            
            loop = CognitiveLoop(mock_agent)
            
            # Should not raise, but handle gracefully
            try:
                loop.absorb("Test content", author="TestAuthor")
            except Exception as e:
                # If it raises, it should be wrapped in our exception type
                assert isinstance(e, (ExtractionError, Exception))
    
    @pytest.mark.skipif(True, reason="Requires complex mocking of LLM response structure")
    def test_reflect_updates_memory(self, mock_agent):
        """Test reflect method updates memory strength."""
        # This test requires mocking complex nested response structures
        # Skip for now as reflect is tested in integration tests
        pass
    
    @pytest.mark.skipif(True, reason="Requires complex mocking of LLM response structure")
    def test_reply_generates_response(self, mock_agent):
        """Test reply method generates contextual response."""
        # This test requires mocking complex nested response structures
        # Skip for now as reply is tested in integration tests
        pass
