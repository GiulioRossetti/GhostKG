# New modular imports (Phase 1 refactoring)
from .fsrs import FSRS, Rating
from .agent import GhostAgent
from .cognitive import CognitiveLoop
from .extraction import FastExtractor, LLMExtractor, get_extractor
from .manager import AgentManager
from .storage import KnowledgeDB, NodeState

# Backward compatibility: Also export from core
# This ensures old code using "from ghost_kg.core import ..." still works
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
]
