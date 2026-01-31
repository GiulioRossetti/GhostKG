"""Backward compatibility shim for ghost_kg.extraction

This module maintains backward compatibility for code that imports directly from ghost_kg.extraction.
New code should import from ghost_kg or ghost_kg.extraction instead.
"""

# Re-export from new location
from .extraction.extraction import *  # noqa: F401, F403
