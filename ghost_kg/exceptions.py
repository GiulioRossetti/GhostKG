"""Backward compatibility shim for ghost_kg.exceptions

This module maintains backward compatibility for code that imports directly from ghost_kg.exceptions.
New code should import from ghost_kg or ghost_kg.utils instead.
"""

# Re-export from new location
from .utils.exceptions import *  # noqa: F401, F403
