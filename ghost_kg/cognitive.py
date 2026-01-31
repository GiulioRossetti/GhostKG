"""Backward compatibility shim for ghost_kg.cognitive

This module maintains backward compatibility for code that imports directly from ghost_kg.cognitive.
New code should import from ghost_kg or ghost_kg.core instead.
"""

# Re-export from new location
from .core.cognitive import *  # noqa: F401, F403
