"""
BACKWARD COMPATIBILITY MODULE

This module maintains backward compatibility for code that imports from ghost_kg.core.
The implementation has been refactored into focused modules:

- ghost_kg.fsrs: FSRS algorithm and Rating enum
- ghost_kg.agent: GhostAgent class
- ghost_kg.cognitive: CognitiveLoop class
- ghost_kg.extraction: Triplet extraction strategies

Old imports will continue to work:
    from ghost_kg.core import GhostAgent, CognitiveLoop, Rating, FSRS

New code should import from specific modules:
    from ghost_kg.fsrs import FSRS, Rating
    from ghost_kg.agent import GhostAgent
    from ghost_kg.cognitive import CognitiveLoop
"""

from .agent import GhostAgent
from .cognitive import CognitiveLoop

# Re-export from new modules for backward compatibility
from .fsrs import FSRS, Rating

__all__ = ["FSRS", "Rating", "GhostAgent", "CognitiveLoop"]
