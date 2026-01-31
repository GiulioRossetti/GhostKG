"""Backward compatibility shim for ghost_kg.dependencies

This module maintains backward compatibility for code that imports directly from ghost_kg.dependencies.
New code should import from ghost_kg or ghost_kg.utils instead.
"""

# Re-export from new location
from .utils.dependencies import *  # noqa: F401, F403
