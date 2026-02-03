"""
LLM Service implementations for unified provider access.

This module provides a unified interface for interacting with different LLM providers,
supporting both local (Ollama) and commercial (OpenAI, Anthropic, etc.) models.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# Optional dependencies for Ollama
try:
    from ollama import Client as OllamaClient

    HAS_OLLAMA = True
except ImportError:
    OllamaClient = None
    HAS_OLLAMA = False

# Optional dependencies for LangChain providers
try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.language_models.chat_models import BaseChatModel

    HAS_LANGCHAIN_CORE = True
except ImportError:
    BaseChatModel = None
    HumanMessage = None
    SystemMessage = None
    HAS_LANGCHAIN_CORE = False


class LLMServiceBase(ABC):
    """
    Abstract base class for LLM services.

    Provides a unified interface for different LLM providers, ensuring
    consistent behavior across local and commercial models.
    """

    @abstractmethod
    def chat(
        self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send a chat request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Optional model override
            **kwargs: Provider-specific options (format, temperature, etc.)

        Returns:
            Dict with response in format: {"message": {"content": str}}

        Raises:
            Exception: On provider-specific errors
        """
        pass

    @abstractmethod
    def get_provider_type(self) -> str:
        """
        Get the provider type identifier.

        Returns:
            str: Provider type (e.g., "ollama", "openai", "anthropic")
        """
        pass


class OllamaLLMService(LLMServiceBase):
    """
    LLM service for local Ollama models.

    Wraps the Ollama client to provide the unified LLMServiceBase interface.
    """

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        """
        Initialize Ollama LLM service.

        Args:
            host: Ollama server URL
            model: Default model name

        Raises:
            ImportError: If ollama package not installed
        """
        if not HAS_OLLAMA:
            raise ImportError(
                "Ollama support requires 'ollama' package. Install with: pip install ollama"
            )
        self.client = OllamaClient(host=host)
        self.default_model = model

    def chat(
        self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send a chat request to Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Optional model override
            **kwargs: Ollama-specific options (format, temperature, etc.)

        Returns:
            Dict with response in Ollama format
        """
        model_to_use = model or self.default_model
        return self.client.chat(model=model_to_use, messages=messages, **kwargs)  # type: ignore[return-value]

    def get_provider_type(self) -> str:
        """Get provider type."""
        return "ollama"


class LangChainLLMService(LLMServiceBase):
    """
    LLM service for LangChain-based commercial providers.

    Supports OpenAI, Anthropic, Google, Cohere, and other LangChain providers.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **provider_kwargs: Any,
    ) -> None:
        """
        Initialize LangChain LLM service.

        Args:
            provider: Provider name ("openai", "anthropic", "google", "cohere")
            model: Model identifier (e.g., "gpt-4", "claude-3-opus-20240229")
            api_key: API key (if None, reads from environment)
            base_url: Optional base URL for API endpoint
            **provider_kwargs: Additional provider-specific parameters

        Raises:
            ImportError: If required LangChain packages not installed
            ValueError: If provider not supported
        """
        if not HAS_LANGCHAIN_CORE:
            raise ImportError(
                "LangChain support requires 'langchain-core'. "
                "Install with: pip install langchain-core"
            )

        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

        # Initialize the appropriate LangChain model
        self.llm = self._create_langchain_model(provider_kwargs)

    def _create_langchain_model(self, provider_kwargs: Dict[str, Any]) -> Any:
        """
        Create LangChain model instance based on provider.

        Args:
            provider_kwargs: Provider-specific configuration

        Returns:
            LangChain chat model instance

        Raises:
            ImportError: If provider package not installed
            ValueError: If provider not supported
        """
        if self.provider == "openai":
            try:
                from langchain_openai import ChatOpenAI

                kwargs = {"model": self.model}
                if self.api_key:
                    kwargs["api_key"] = self.api_key
                elif os.getenv("OPENAI_API_KEY"):
                    kwargs["api_key"] = os.getenv("OPENAI_API_KEY")
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                kwargs.update(provider_kwargs)
                return ChatOpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "OpenAI support requires 'langchain-openai'. "
                    "Install with: pip install langchain-openai"
                )

        elif self.provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic

                kwargs = {"model": self.model}
                if self.api_key:
                    kwargs["anthropic_api_key"] = self.api_key
                elif os.getenv("ANTHROPIC_API_KEY"):
                    kwargs["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
                if self.base_url:
                    kwargs["anthropic_api_url"] = self.base_url
                kwargs.update(provider_kwargs)
                return ChatAnthropic(**kwargs)
            except ImportError:
                raise ImportError(
                    "Anthropic support requires 'langchain-anthropic'. "
                    "Install with: pip install langchain-anthropic"
                )

        elif self.provider == "google":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                kwargs = {"model": self.model}
                if self.api_key:
                    kwargs["google_api_key"] = self.api_key
                elif os.getenv("GOOGLE_API_KEY"):
                    kwargs["google_api_key"] = os.getenv("GOOGLE_API_KEY")
                kwargs.update(provider_kwargs)
                return ChatGoogleGenerativeAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "Google support requires 'langchain-google-genai'. "
                    "Install with: pip install langchain-google-genai"
                )

        elif self.provider == "cohere":
            try:
                from langchain_cohere import ChatCohere

                kwargs = {"model": self.model}
                if self.api_key:
                    kwargs["cohere_api_key"] = self.api_key
                elif os.getenv("COHERE_API_KEY"):
                    kwargs["cohere_api_key"] = os.getenv("COHERE_API_KEY")
                kwargs.update(provider_kwargs)
                return ChatCohere(**kwargs)
            except ImportError:
                raise ImportError(
                    "Cohere support requires 'langchain-cohere'. "
                    "Install with: pip install langchain-cohere"
                )

        else:
            raise ValueError(
                f"Unsupported provider: {self.provider}. "
                f"Supported providers: openai, anthropic, google, cohere"
            )

    def chat(
        self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send a chat request to LangChain provider.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Optional model override (not used, model set at init)
            **kwargs: LangChain-specific options

        Returns:
            Dict with response in Ollama-compatible format

        Note:
            Response is converted to Ollama format for backward compatibility:
            {"message": {"content": str}}
        """
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))  # type: ignore[misc]
            else:
                langchain_messages.append(HumanMessage(content=content))  # type: ignore[misc]

        # Call LangChain model
        response = self.llm.invoke(langchain_messages, **kwargs)

        # Convert to Ollama-compatible format
        return {"message": {"content": response.content}}

    def get_provider_type(self) -> str:
        """Get provider type."""
        return self.provider


def get_llm_service(
    provider: str = "ollama",
    model: str = "llama3.2",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs: Any,
) -> LLMServiceBase:
    """
    Factory function to create appropriate LLM service.

    Args:
        provider: Provider name ("ollama", "openai", "anthropic", "google", "cohere")
        model: Model identifier
        api_key: API key for commercial providers (if None, reads from environment)
        base_url: Optional base URL (for Ollama host or API endpoint override)
        **kwargs: Additional provider-specific parameters

    Returns:
        LLMServiceBase instance

    Raises:
        ImportError: If required packages not installed
        ValueError: If provider not supported

    Examples:
        >>> # Local Ollama
        >>> service = get_llm_service("ollama", "llama3.2")
        
        >>> # OpenAI
        >>> service = get_llm_service("openai", "gpt-4", api_key="sk-...")
        
        >>> # Anthropic
        >>> service = get_llm_service("anthropic", "claude-3-opus-20240229")
        
        >>> # Google
        >>> service = get_llm_service("google", "gemini-pro")
    """
    provider = provider.lower()

    if provider == "ollama":
        host = base_url or kwargs.pop("host", "http://localhost:11434")
        return OllamaLLMService(host=host, model=model)
    else:
        return LangChainLLMService(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )
