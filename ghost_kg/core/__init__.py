"""Core agent and manager functionality."""

from .agent import GhostAgent
from .cognitive import CognitiveLoop
from .manager import AgentManager

__all__ = [
    "GhostAgent",
    "CognitiveLoop",
    "AgentManager",
]
