# AgentManager API

The `AgentManager` class provides a high-level interface for managing multiple agents and their knowledge graphs.

## Module Location

```python
# Recommended: Import from top-level package
from ghost_kg import AgentManager, Rating

# Also supported: Import from subpackage
from ghost_kg.core import AgentManager

# Backward compatible: Old flat import
from ghost_kg.manager import AgentManager
```

## Overview

AgentManager is the primary entry point for external programs to interact with GhostKG. It allows you to:

- Create and manage multiple agents
- Update agent knowledge graphs with new content
- Retrieve context for generating responses
- Update knowledge graphs with generated responses
- Control simulation time for each agent

## Basic Usage

```python
from ghost_kg import AgentManager, Rating
import datetime

# Initialize manager
manager = AgentManager(db_path="agents.db")

# Create agents
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# Set simulation time
current_time = datetime.datetime.now(datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)

# Add knowledge
manager.learn_triplet("Alice", "I", "support", "UBI", rating=Rating.Easy, sentiment=0.8)

# Process content
manager.absorb_content(
    "Alice",
    "Bob mentioned automation",
    author="Bob",
    triplets=[("Bob", "mentions", "automation")]
)

# Get context
context = manager.get_context("Alice", topic="UBI")
```

## API Reference

::: ghost_kg.manager.AgentManager
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
