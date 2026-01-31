"""Backward compatibility shim for ghost_kg.storage

This module maintains backward compatibility for code that imports directly from ghost_kg.storage.
New code should import from ghost_kg or ghost_kg.storage instead.
"""

# Re-export from new location
from .storage.database import *  # noqa: F401, F403
