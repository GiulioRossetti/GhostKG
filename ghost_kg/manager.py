"""Backward compatibility shim for ghost_kg.manager

This module maintains backward compatibility for code that imports directly from ghost_kg.manager.
New code should import from ghost_kg or ghost_kg.core instead.
"""

# Re-export from new location
from .core.manager import *  # noqa: F401, F403
