"""Custom exceptions for GhostKG.

This module defines a hierarchy of exceptions used throughout the GhostKG package
to provide clear, specific error messages and enable proper error handling.
"""


class GhostKGError(Exception):
    """Base exception for all GhostKG errors.
    
    All custom exceptions in GhostKG inherit from this base class,
    making it easy to catch all GhostKG-specific errors.
    """
    pass


class DatabaseError(GhostKGError):
    """Database operation failed.
    
    Raised when SQLite operations fail, such as:
    - Connection errors
    - Query execution errors
    - Transaction failures
    - Constraint violations
    """
    pass


class LLMError(GhostKGError):
    """LLM operation failed.
    
    Raised when LLM (Large Language Model) operations fail, such as:
    - Connection timeouts
    - API errors
    - Invalid responses
    - Model not available
    """
    pass


class ExtractionError(GhostKGError):
    """Triplet extraction failed.
    
    Raised when triplet extraction from text fails, such as:
    - Invalid JSON in LLM response
    - Missing required fields
    - Extraction timeout
    - Model initialization failure
    """
    pass


class ConfigurationError(GhostKGError):
    """Configuration invalid or missing.
    
    Raised when configuration is invalid, such as:
    - Invalid parameter values
    - Missing required configuration
    - Incompatible settings
    """
    pass


class AgentNotFoundError(GhostKGError):
    """Agent does not exist.
    
    Raised when attempting to access a non-existent agent, such as:
    - Querying unknown agent
    - Operating on deleted agent
    """
    pass


class ValidationError(GhostKGError):
    """Input validation failed.
    
    Raised when input parameters fail validation, such as:
    - Invalid types
    - Out of range values
    - Malformed data
    - Missing required fields
    """
    pass


class DependencyError(GhostKGError):
    """Required dependency not available.
    
    Raised when an optional dependency is required but not installed, such as:
    - Missing GLiNER for fast mode
    - Missing Ollama for LLM mode
    - Missing TextBlob for sentiment analysis
    """
    pass
