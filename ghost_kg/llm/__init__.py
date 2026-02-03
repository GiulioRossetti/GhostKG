"""
LLM Service Module

This module provides a unified interface for interacting with various LLM providers:
- Local models via Ollama
- Commercial providers via LangChain (OpenAI, Anthropic, Google, Cohere, etc.)

The module includes:
- LLMServiceBase: Abstract base class for all LLM services
- OllamaLLMService: Service for local Ollama models
- LangChainLLMService: Service for LangChain-based commercial providers
- get_llm_service: Factory function to create appropriate service
"""

from .service import LLMServiceBase, OllamaLLMService, LangChainLLMService, get_llm_service

__all__ = [
    "LLMServiceBase",
    "OllamaLLMService",
    "LangChainLLMService",
    "get_llm_service",
]
