# New modular imports (Phase 1 refactoring)
# Backward compatibility: Also export from core
# This ensures old code using "from ghost_kg.core import ..." still works
from . import core
from .agent import GhostAgent

# Phase 7: Performance optimization
from .cache import AgentCache, clear_global_cache, get_global_cache
from .cognitive import CognitiveLoop

# Phase 4: Configuration management
from .config import (
    DatabaseConfig,
    FastModeConfig,
    FSRSConfig,
    GhostKGConfig,
    LLMConfig,
    get_default_config,
)

# Phase 2: Dependency management
from .dependencies import DependencyChecker, has_fast_support, has_llm_support

# Phase 3: Error handling
from .exceptions import (
    AgentNotFoundError,
    ConfigurationError,
    DatabaseError,
    DependencyError,
    ExtractionError,
    GhostKGError,
    LLMError,
    ValidationError,
)
from .extraction import FastExtractor, LLMExtractor, get_extractor
from .fsrs import FSRS, Rating
from .manager import AgentManager
from .storage import KnowledgeDB, NodeState

__all__ = [
    # Core classes
    "GhostAgent",
    "CognitiveLoop",
    "Rating",
    "FSRS",
    # Manager API
    "AgentManager",
    # Storage
    "KnowledgeDB",
    "NodeState",
    # Extraction strategies
    "FastExtractor",
    "LLMExtractor",
    "get_extractor",
    # Dependency checking (Phase 2)
    "DependencyChecker",
    "has_llm_support",
    "has_fast_support",
    # Exceptions (Phase 3)
    "GhostKGError",
    "DatabaseError",
    "LLMError",
    "ExtractionError",
    "ConfigurationError",
    "AgentNotFoundError",
    "ValidationError",
    "DependencyError",
    # Configuration (Phase 4)
    "FSRSConfig",
    "DatabaseConfig",
    "LLMConfig",
    "FastModeConfig",
    "GhostKGConfig",
    "get_default_config",
    # Performance/Caching (Phase 7)
    "AgentCache",
    "get_global_cache",
    "clear_global_cache",
]
