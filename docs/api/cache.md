# Cache API

The cache module provides LRU caching for agent contexts and memory views to improve query performance.

## Module Location

```python
# Recommended: Import from top-level package
from ghost_kg import AgentCache, get_global_cache, clear_global_cache

# Also supported: Import from subpackage
from ghost_kg.memory import AgentCache, get_global_cache, clear_global_cache

# Backward compatible: Old flat import
from ghost_kg.cache import AgentCache, get_global_cache, clear_global_cache
```

## Overview

The caching system includes:

- **AgentCache**: Thread-safe LRU cache for agent data
- **Global cache instance**: Shared cache across the application
- **Automatic eviction**: Removes least recently used items
- **Thread safety**: Safe for concurrent access

## Features

- **LRU eviction**: Automatically removes old entries when capacity is reached
- **TTL support**: Optional time-to-live for cache entries
- **Statistics**: Track hit/miss rates for performance monitoring
- **Thread-safe**: Uses RLock for concurrent access

## Basic Usage

```python
from ghost_kg.cache import AgentCache, get_global_cache, clear_global_cache

# Use global cache
cache = get_global_cache()

# Store context in cache
cache.put_context(
    agent_name="Alice",
    topic="climate",
    context="Climate action is urgent..."
)

# Retrieve context
context = cache.get_context("Alice", "climate")
if context:
    print(f"Cache hit: {context}")
else:
    print("Cache miss")

# Store memory view
memories = [("climate_change", 0.85, "supports")]
cache.put_memory_view("Alice", "climate", memories)

# Retrieve memory view
cached_memories = cache.get_memory_view("Alice", "climate")

# Get cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Size: {stats['size']}/{stats['capacity']}")

# Clear cache
cache.clear()

# Clear global cache
clear_global_cache()
```

## Cache Configuration

```python
# Create cache with custom capacity
cache = AgentCache(capacity=200)

# Create cache with TTL
cache = AgentCache(capacity=100, ttl_seconds=3600)
```

## Performance

Caching provides significant performance improvements:

- **First query**: ~50-100ms (database query)
- **Cached query**: ~0.1ms (memory lookup)
- **Speedup**: 500-1000x faster

## Thread Safety

The cache is thread-safe and can be used in multi-threaded applications:

```python
from concurrent.futures import ThreadPoolExecutor
from ghost_kg.cache import get_global_cache

cache = get_global_cache()

def worker(agent_name, topic):
    cache.put_context(agent_name, topic, "context")
    return cache.get_context(agent_name, topic)

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(worker, f"Agent{i}", "topic")
        for i in range(100)
    ]
    results = [f.result() for f in futures]
```

## API Reference

::: ghost_kg.cache.AgentCache
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.cache.get_global_cache
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: ghost_kg.cache.clear_global_cache
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
