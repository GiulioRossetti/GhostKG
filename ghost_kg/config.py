"""Backward compatibility shim for ghost_kg.config

This module maintains backward compatibility for code that imports directly from ghost_kg.config.
New code should import from ghost_kg or ghost_kg.utils instead.
"""

# Re-export from new location
from .utils.config import *  # noqa: F401, F403
