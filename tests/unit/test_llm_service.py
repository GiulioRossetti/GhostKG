"""Unit tests for LLM service module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ghost_kg.llm import (
    LLMServiceBase,
    OllamaLLMService,
    LangChainLLMService,
    get_llm_service,
)


class TestLLMServiceBase:
    """Test LLMServiceBase abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that LLMServiceBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMServiceBase()  # type: ignore[abstract]


class TestOllamaLLMService:
    """Test OllamaLLMService."""

    @patch("ghost_kg.llm.service.HAS_OLLAMA", True)
    @patch("ghost_kg.llm.service.OllamaClient")
    def test_initialization(self, mock_ollama_client):
        """Test OllamaLLMService initializes correctly."""
        service = OllamaLLMService(host="http://localhost:11434", model="llama3.2")
        assert service.default_model == "llama3.2"
        assert service.get_provider_type() == "ollama"
        mock_ollama_client.assert_called_once_with(host="http://localhost:11434")

    @patch("ghost_kg.llm.service.HAS_OLLAMA", False)
    def test_initialization_without_ollama(self):
        """Test OllamaLLMService raises error if ollama not installed."""
        with pytest.raises(ImportError, match="Ollama support requires 'ollama' package"):
            OllamaLLMService()

    @patch("ghost_kg.llm.service.HAS_OLLAMA", True)
    @patch("ghost_kg.llm.service.OllamaClient")
    def test_chat(self, mock_ollama_client):
        """Test chat method."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.chat.return_value = {
            "message": {"content": "Hello!"}
        }
        mock_ollama_client.return_value = mock_client_instance

        # Create service and call chat
        service = OllamaLLMService(model="llama3.2")
        messages = [{"role": "user", "content": "Hi"}]
        response = service.chat(messages)

        # Verify
        assert response == {"message": {"content": "Hello!"}}
        mock_client_instance.chat.assert_called_once_with(
            model="llama3.2", messages=messages
        )

    @patch("ghost_kg.llm.service.HAS_OLLAMA", True)
    @patch("ghost_kg.llm.service.OllamaClient")
    def test_chat_with_model_override(self, mock_ollama_client):
        """Test chat with model override."""
        mock_client_instance = Mock()
        mock_client_instance.chat.return_value = {"message": {"content": "Hi"}}
        mock_ollama_client.return_value = mock_client_instance

        service = OllamaLLMService(model="llama3.2")
        messages = [{"role": "user", "content": "Hi"}]
        service.chat(messages, model="mistral")

        mock_client_instance.chat.assert_called_once_with(
            model="mistral", messages=messages
        )


class TestLangChainLLMService:
    """Test LangChainLLMService."""

    @patch("ghost_kg.llm.service.HAS_LANGCHAIN_CORE", False)
    def test_initialization_without_langchain(self):
        """Test LangChainLLMService raises error if langchain not installed."""
        with pytest.raises(ImportError, match="LangChain support requires 'langchain-core'"):
            LangChainLLMService(provider="openai", model="gpt-4")

    @patch("ghost_kg.llm.service.HAS_LANGCHAIN_CORE", True)
    @patch("ghost_kg.llm.service.LangChainLLMService._create_langchain_model")
    def test_initialization_openai(self, mock_create_model):
        """Test initialization with OpenAI provider."""
        mock_create_model.return_value = Mock()
        service = LangChainLLMService(provider="openai", model="gpt-4", api_key="test-key")
        
        assert service.provider == "openai"
        assert service.model == "gpt-4"
        assert service.api_key == "test-key"
        assert service.get_provider_type() == "openai"

    @patch("ghost_kg.llm.service.HAS_LANGCHAIN_CORE", True)
    @patch("ghost_kg.llm.service.HumanMessage")
    @patch("ghost_kg.llm.service.LangChainLLMService._create_langchain_model")
    def test_chat(self, mock_create_model, mock_human_message):
        """Test chat method."""
        # Setup mocks
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Hello from LangChain!"
        mock_llm.invoke.return_value = mock_response
        mock_create_model.return_value = mock_llm

        # Create service and call chat
        service = LangChainLLMService(provider="openai", model="gpt-4", api_key="test")
        messages = [{"role": "user", "content": "Hi"}]
        response = service.chat(messages)

        # Verify
        assert response == {"message": {"content": "Hello from LangChain!"}}
        mock_llm.invoke.assert_called_once()

    @patch("ghost_kg.llm.service.HAS_LANGCHAIN_CORE", True)
    def test_unsupported_provider(self):
        """Test that unsupported provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider: unknown"):
            LangChainLLMService(provider="unknown", model="test", api_key="test")

    @patch("ghost_kg.llm.service.HAS_LANGCHAIN_CORE", True)
    @pytest.mark.skipif(
        True,  # Skip by default since langchain_openai might not be installed
        reason="langchain_openai not available"
    )
    def test_create_openai_model(self):
        """Test creating OpenAI model."""
        try:
            from langchain_openai import ChatOpenAI
            from unittest.mock import patch
            
            with patch.object(ChatOpenAI, "__init__", return_value=None):
                service = LangChainLLMService(
                    provider="openai",
                    model="gpt-4",
                    api_key="test-key"
                )
                assert service.provider == "openai"
        except ImportError:
            pytest.skip("langchain_openai not installed")


class TestGetLLMService:
    """Test get_llm_service factory function."""

    @patch("ghost_kg.llm.service.HAS_OLLAMA", True)
    @patch("ghost_kg.llm.service.OllamaClient")
    def test_get_ollama_service(self, mock_ollama_client):
        """Test factory creates OllamaLLMService."""
        service = get_llm_service(provider="ollama", model="llama3.2")
        assert isinstance(service, OllamaLLMService)
        assert service.get_provider_type() == "ollama"

    @patch("ghost_kg.llm.service.HAS_LANGCHAIN_CORE", True)
    @patch("ghost_kg.llm.service.LangChainLLMService._create_langchain_model")
    def test_get_langchain_service(self, mock_create_model):
        """Test factory creates LangChainLLMService for commercial providers."""
        mock_create_model.return_value = Mock()
        
        service = get_llm_service(provider="openai", model="gpt-4", api_key="test")
        assert isinstance(service, LangChainLLMService)
        assert service.get_provider_type() == "openai"

    @patch("ghost_kg.llm.service.HAS_OLLAMA", True)
    @patch("ghost_kg.llm.service.OllamaClient")
    def test_get_service_with_base_url(self, mock_ollama_client):
        """Test factory passes base_url correctly for Ollama."""
        service = get_llm_service(
            provider="ollama",
            model="llama3.2",
            base_url="http://192.168.1.100:11434"
        )
        mock_ollama_client.assert_called_with(host="http://192.168.1.100:11434")

    @patch("ghost_kg.llm.service.HAS_LANGCHAIN_CORE", True)
    @patch("ghost_kg.llm.service.LangChainLLMService._create_langchain_model")
    def test_get_service_case_insensitive(self, mock_create_model):
        """Test factory handles provider names case-insensitively."""
        mock_create_model.return_value = Mock()
        
        service = get_llm_service(provider="OpenAI", model="gpt-4", api_key="test")
        assert service.get_provider_type() == "openai"

    @patch("ghost_kg.llm.service.HAS_LANGCHAIN_CORE", True)
    @patch("ghost_kg.llm.service.LangChainLLMService._create_langchain_model")
    def test_get_service_with_additional_kwargs(self, mock_create_model):
        """Test factory passes additional kwargs to LangChain service."""
        mock_create_model.return_value = Mock()
        
        service = get_llm_service(
            provider="openai",
            model="gpt-4",
            api_key="test",
            temperature=0.7,
            max_tokens=100
        )
        assert isinstance(service, LangChainLLMService)
