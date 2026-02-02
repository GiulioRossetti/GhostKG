"""GhostKG - Dynamic Knowledge Graphs with Memory Decay for LLM Agents

This package provides dynamic knowledge graph management for LLM agents with built-in
memory decay using FSRS (Free Spaced Repetition Scheduler).

Main API:
---------
Core functionality:
  - AgentManager: High-level API for managing agents
  - GhostAgent: Individual agent with knowledge graph
  - CognitiveLoop: Agent cognitive operations

Memory system:
  - FSRS: Spaced repetition algorithm
  - Rating: Memory rating enum
  - AgentCache: Performance caching

Storage:
  - KnowledgeDB: Database management
  - NodeState: Memory state tracking

Extraction:
  - FastExtractor: Fast GLiNER-based extraction
  - LLMExtractor: LLM-based extraction
  - get_extractor: Factory function

Utilities:
  - Configuration classes (FSRSConfig, DatabaseConfig, etc.)
  - Exception classes (GhostKGError, DatabaseError, etc.)
  - Dependency checking (has_fast_support, has_llm_support)

Package Structure:
------------------
- ghost_kg.core: Core agent and manager functionality
- ghost_kg.memory: Memory management (FSRS, caching)
- ghost_kg.storage: Database and persistence
- ghost_kg.extraction: Triplet extraction strategies
- ghost_kg.utils: Configuration, exceptions, dependencies
"""

# Import from subpackages
from .core import AgentManager, CognitiveLoop, GhostAgent
from .extraction import FastExtractor, LLMExtractor, get_extractor
from .memory import FSRS, AgentCache, Rating, clear_global_cache, get_global_cache
from .storage import KnowledgeDB, NodeState
from .utils import (
    AgentNotFoundError,
    ConfigurationError,
    DatabaseConfig,
    DatabaseError,
    DependencyChecker,
    DependencyError,
    ExtractionError,
    FSRSConfig,
    FastModeConfig,
    GhostKGConfig,
    GhostKGError,
    LLMConfig,
    LLMError,
    ValidationError,
    get_default_config,
    has_fast_support,
    has_llm_support,
)
from .utils.time_utils import SimulationTime, parse_time_input

# Backward compatibility: Also export core module for old imports
from . import core

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
    # Dependency checking
    "DependencyChecker",
    "has_llm_support",
    "has_fast_support",
    # Exceptions
    "GhostKGError",
    "DatabaseError",
    "LLMError",
    "ExtractionError",
    "ConfigurationError",
    "AgentNotFoundError",
    "ValidationError",
    "DependencyError",
    # Configuration
    "FSRSConfig",
    "DatabaseConfig",
    "LLMConfig",
    "FastModeConfig",
    "GhostKGConfig",
    "get_default_config",
    # Performance/Caching
    "AgentCache",
    "get_global_cache",
    "clear_global_cache",
    # Time utilities
    "SimulationTime",
    "parse_time_input",
    # Backward compatibility
    "core",
]

__version__ = "0.2.0"
