"""Backward compatibility shim for ghost_kg.cache

This module maintains backward compatibility for code that imports directly from ghost_kg.cache.
New code should import from ghost_kg or ghost_kg.memory instead.
"""

# Re-export from new location
from .memory.cache import *  # noqa: F401, F403
