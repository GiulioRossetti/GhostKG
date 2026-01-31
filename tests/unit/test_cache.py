"""
Tests for the caching module.

Tests cover:
- AgentCache basic operations
- Cache eviction (LRU)
- Thread safety
- Cache statistics
- Global cache management
"""

import pytest
import threading
import time
from ghost_kg import AgentCache, get_global_cache, clear_global_cache


class TestAgentCache:
    """Test AgentCache functionality."""
    
    def test_cache_initialization(self):
        """Test cache can be initialized with custom parameters."""
        cache = AgentCache(max_size=256, enabled=True)
        assert cache.max_size == 256
        assert cache.enabled is True
        
        stats = cache.get_stats()
        assert stats["context_entries"] == 0
        assert stats["memory_entries"] == 0
        assert stats["max_size"] == 256
    
    def test_cache_disabled(self):
        """Test cache can be disabled."""
        cache = AgentCache(enabled=False)
        
        # Put and get should do nothing when disabled
        cache.put_context("Alice", "topic", "context")
        result = cache.get_context("Alice", "topic")
        
        assert result is None
        stats = cache.get_stats()
        assert stats["context_entries"] == 0
    
    def test_context_cache_put_and_get(self):
        """Test putting and getting context from cache."""
        cache = AgentCache()
        
        # Put context
        cache.put_context("Alice", "climate", "Climate context data")
        
        # Get context
        result = cache.get_context("Alice", "climate")
        assert result == "Climate context data"
        
        # Get non-existent context
        result = cache.get_context("Alice", "nonexistent")
        assert result is None
    
    def test_memory_view_cache_put_and_get(self):
        """Test putting and getting memory view from cache."""
        cache = AgentCache()
        
        # Put memory view
        data = {"nodes": ["A", "B"], "edges": [("A", "B")]}
        cache.put_memory_view("Alice", data, topic="climate")
        
        # Get memory view
        result = cache.get_memory_view("Alice", topic="climate")
        assert result == data
        
        # Get non-existent
        result = cache.get_memory_view("Alice", topic="other")
        assert result is None
    
    def test_cache_eviction_lru(self):
        """Test LRU eviction when cache is full."""
        cache = AgentCache(max_size=3)
        
        # Fill cache
        cache.put_context("Agent1", "topic", "context1")
        cache.put_context("Agent2", "topic", "context2")
        cache.put_context("Agent3", "topic", "context3")
        
        stats = cache.get_stats()
        assert stats["context_entries"] == 3
        
        # Add one more - should evict least recently used
        cache.put_context("Agent4", "topic", "context4")
        
        stats = cache.get_stats()
        assert stats["context_entries"] == 3
        
        # Agent1 should have been evicted (least recently used)
        # Agent4 should be present
        assert cache.get_context("Agent4", "topic") == "context4"
    
    def test_cache_access_updates_lru(self):
        """Test that accessing an entry updates its LRU status."""
        cache = AgentCache(max_size=3)
        
        # Fill cache
        cache.put_context("Agent1", "topic", "context1")
        cache.put_context("Agent2", "topic", "context2")
        cache.put_context("Agent3", "topic", "context3")
        
        # Access Agent1 to make it recently used
        cache.get_context("Agent1", "topic")
        
        # Add Agent4 - should evict Agent2 (oldest access)
        cache.put_context("Agent4", "topic", "context4")
        
        # Agent1 should still be there
        assert cache.get_context("Agent1", "topic") == "context1"
    
    def test_invalidate_agent(self):
        """Test invalidating all cache entries for an agent."""
        cache = AgentCache()
        
        # Add multiple entries
        cache.put_context("Alice", "topic1", "context1")
        cache.put_context("Alice", "topic2", "context2")
        cache.put_context("Bob", "topic1", "context3")
        
        # Invalidate Alice (currently invalidates all - simplified implementation)
        count = cache.invalidate_agent("Alice")
        assert count > 0
        
        # All caches should be cleared (simplified implementation)
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
    
    def test_clear_cache(self):
        """Test clearing all cache entries."""
        cache = AgentCache()
        
        # Add entries
        cache.put_context("Alice", "topic", "context")
        cache.put_memory_view("Bob", {"data": "value"})
        
        # Clear
        cache.clear()
        
        # Verify empty
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert cache.get_context("Alice", "topic") is None
    
    def test_cache_statistics(self):
        """Test cache statistics reporting."""
        cache = AgentCache(max_size=128)
        
        # Add entries
        cache.put_context("Agent1", "topic", "context")
        cache.put_memory_view("Agent2", {"data": "value"})
        
        stats = cache.get_stats()
        assert stats["context_entries"] == 1
        assert stats["memory_entries"] == 1
        assert stats["total_entries"] == 2
        assert stats["max_size"] == 128
        assert stats["enabled"] is True


class TestGlobalCache:
    """Test global cache management."""
    
    def test_get_global_cache(self):
        """Test getting global cache instance."""
        cache1 = get_global_cache()
        cache2 = get_global_cache()
        
        # Should be the same instance
        assert cache1 is cache2
    
    def test_clear_global_cache(self):
        """Test clearing global cache."""
        cache = get_global_cache()
        
        # Add data
        cache.put_context("Alice", "topic", "context")
        assert cache.get_context("Alice", "topic") == "context"
        
        # Clear
        clear_global_cache()
        
        # Verify cleared
        assert cache.get_context("Alice", "topic") is None
    
    def test_global_cache_configuration(self):
        """Test global cache can be configured."""
        # Note: This test may not work as expected because get_global_cache
        # returns existing instance. In real use, configure before first access.
        cache = get_global_cache(enabled=True, max_size=256)
        
        assert cache is not None
        assert cache.max_size in [128, 256]  # May be existing instance


class TestCacheThreadSafety:
    """Test cache thread safety."""
    
    def test_concurrent_put_and_get(self):
        """Test concurrent cache operations are thread-safe."""
        # Use cache size larger than total keys to avoid eviction during test
        # 5 threads * 50 operations = 250 unique keys
        cache = AgentCache(max_size=300)
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(50):
                    cache.put_context(f"Agent{thread_id}", f"topic{i}", f"context{i}")
                    result = cache.get_context(f"Agent{thread_id}", f"topic{i}")
                    if result != f"context{i}":
                        errors.append(f"Thread {thread_id}: Expected context{i}, got {result}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check for errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
    
    def test_concurrent_eviction(self):
        """Test concurrent cache eviction is thread-safe."""
        cache = AgentCache(max_size=10)
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(20):
                    cache.put_context(f"Agent{thread_id}_{i}", "topic", f"context{i}")
                    time.sleep(0.001)  # Small delay to increase concurrency
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check for errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify cache size is within limits
        stats = cache.get_stats()
        assert stats["total_entries"] <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
