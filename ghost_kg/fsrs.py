"""Backward compatibility shim for ghost_kg.fsrs

This module maintains backward compatibility for code that imports directly from ghost_kg.fsrs.
New code should import from ghost_kg or ghost_kg.memory instead.
"""

# Re-export from new location
from .memory.fsrs import *  # noqa: F401, F403
