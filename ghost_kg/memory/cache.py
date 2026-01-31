"""
Caching layer for frequently accessed data in GhostKG.

This module provides caching mechanisms to improve performance by reducing
repeated database queries and expensive computations.
"""

import hashlib
import json
import threading
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple


class AgentCache:
    """
    Thread-safe cache for agent data with LRU eviction.

    This cache stores frequently accessed data like context retrievals,
    memory views, and query results to reduce database load and improve
    response times.

    The cache is thread-safe and uses LRU (Least Recently Used) eviction
    when it reaches max_size.

    Attributes:
        max_size: Maximum number of entries to cache
        enabled: Whether caching is enabled

    Example:
        >>> cache = AgentCache(max_size=256)
        >>> cache.put_context("Alice", "climate", "context data...")
        >>> context = cache.get_context("Alice", "climate")
        >>> cache.invalidate_agent("Alice")  # Clear Alice's cache
    """

    def __init__(self, max_size: int = 128, enabled: bool = True):
        """
        Initialize the cache.

        Args:
            max_size (int): Maximum number of entries to cache (default: 128)
            enabled (bool): Whether caching is enabled (default: True)

        Returns:
            None
        """
        self.max_size = max_size
        self.enabled = enabled
        self._context_cache: Dict[str, Tuple[str, int]] = {}  # key -> (value, access_count)
        self._memory_cache: Dict[str, Tuple[Any, int]] = {}
        self._lock = threading.Lock()
        self._access_counter = 0

    def _make_key(self, *args) -> str:
        """
        Create a cache key from arguments.

        Args:
            *args: Arguments to hash into a key

        Returns:
            str: Hash string for cache key
        """
        key_str = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _evict_lru(self, cache: Dict[str, Tuple[Any, int]]) -> None:
        """
        Evict least recently used entry from cache.

        Args:
            cache (Dict[str, Tuple[Any, int]]): The cache dict to evict from

        Returns:
            None
        """
        if len(cache) >= self.max_size:
            # Find entry with lowest access count
            lru_key = min(cache.items(), key=lambda x: x[1][1])[0]
            del cache[lru_key]

    def get_context(self, agent_name: str, topic: str) -> Optional[str]:
        """
        Get cached context for agent and topic.

        Args:
            agent_name (str): Name of the agent
            topic (str): Topic keyword

        Returns:
            Optional[str]: Cached context string or None if not found
        """
        if not self.enabled:
            return None

        key = self._make_key("context", agent_name, topic)
        with self._lock:
            if key in self._context_cache:
                value, _ = self._context_cache[key]
                self._access_counter += 1
                self._context_cache[key] = (value, self._access_counter)
                return value
        return None

    def put_context(self, agent_name: str, topic: str, context: str) -> None:
        """
        Cache context for agent and topic.

        Args:
            agent_name (str): Name of the agent
            topic (str): Topic keyword
            context (str): Context string to cache

        Returns:
            None
        """
        if not self.enabled:
            return

        key = self._make_key("context", agent_name, topic)
        with self._lock:
            # Only evict if adding a NEW entry would exceed max_size
            if key not in self._context_cache and len(self._context_cache) >= self.max_size:
                self._evict_lru(self._context_cache)
            self._access_counter += 1
            self._context_cache[key] = (context, self._access_counter)

    def get_memory_view(
        self, agent_name: str, topic: Optional[str] = None, time_filter: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get cached memory view for agent.

        Args:
            agent_name (str): Name of the agent
            topic (Optional[str]): Optional topic filter
            time_filter (Optional[str]): Optional time filter

        Returns:
            Optional[Any]: Cached memory view or None if not found
        """
        if not self.enabled:
            return None

        key = self._make_key("memory", agent_name, topic, time_filter)
        with self._lock:
            if key in self._memory_cache:
                value, _ = self._memory_cache[key]
                self._access_counter += 1
                self._memory_cache[key] = (value, self._access_counter)
                return value
        return None

    def put_memory_view(
        self,
        agent_name: str,
        data: Any,
        topic: Optional[str] = None,
        time_filter: Optional[str] = None,
    ) -> None:
        """
        Cache memory view for agent.

        Args:
            agent_name (str): Name of the agent
            data (Any): Memory view data to cache
            topic (Optional[str]): Optional topic filter
            time_filter (Optional[str]): Optional time filter

        Returns:
            None
        """
        if not self.enabled:
            return

        key = self._make_key("memory", agent_name, topic, time_filter)
        with self._lock:
            # Only evict if adding a NEW entry would exceed max_size
            if key not in self._memory_cache and len(self._memory_cache) >= self.max_size:
                self._evict_lru(self._memory_cache)
            self._access_counter += 1
            self._memory_cache[key] = (data, self._access_counter)

    def invalidate_agent(self, agent_name: str) -> int:
        """
        Invalidate all cache entries for an agent.

        This should be called whenever an agent's knowledge is updated
        to ensure fresh data on next access.

        Args:
            agent_name (str): Name of the agent to invalidate

        Returns:
            int: Number of entries invalidated
        """
        count = 0
        with self._lock:
            # Remove all entries containing this agent name
            keys_to_remove = []

            # Check context cache
            for key in self._context_cache:
                # The key contains agent_name, so we can't directly check
                # but we track keys to remove
                keys_to_remove.append(key)

            # For simplicity, we'll clear all caches when invalidating
            # In production, you'd want to store agent_name separately
            count = len(self._context_cache) + len(self._memory_cache)
            self._context_cache.clear()
            self._memory_cache.clear()

        return count

    def clear(self) -> None:
        """
        Clear all cache entries.

        Returns:
            None
        """
        with self._lock:
            self._context_cache.clear()
            self._memory_cache.clear()
            self._access_counter = 0

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict[str, int]: Dictionary with cache statistics
        """
        with self._lock:
            return {
                "context_entries": len(self._context_cache),
                "memory_entries": len(self._memory_cache),
                "total_entries": len(self._context_cache) + len(self._memory_cache),
                "max_size": self.max_size,
                "enabled": self.enabled,
            }


# Global cache instance (can be disabled or configured)
_global_cache: Optional[AgentCache] = None
_cache_lock = threading.Lock()


def get_global_cache(enabled: bool = True, max_size: int = 128) -> AgentCache:
    """
    Get or create the global cache instance.

    Args:
        enabled (bool): Whether caching is enabled
        max_size (int): Maximum cache size

    Returns:
        AgentCache: Global AgentCache instance
    """
    global _global_cache

    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = AgentCache(max_size=max_size, enabled=enabled)

    return _global_cache


def clear_global_cache() -> None:
    """
    Clear the global cache.

    Returns:
        None
    """
    global _global_cache
    if _global_cache is not None:
        _global_cache.clear()
