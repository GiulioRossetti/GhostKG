# GhostAgent API

The `GhostAgent` class represents an autonomous agent with its own knowledge graph, memory system, and learning capabilities.

## Module Location

```python
# Recommended: Import from top-level package
from ghost_kg import GhostAgent, Rating

# Also supported: Import from subpackage
from ghost_kg.core import GhostAgent

# Backward compatible: Old flat import
from ghost_kg.agent import GhostAgent
```

## Overview

Each GhostAgent maintains:

- **Personal knowledge graph** with semantic triplets (subject-relation-object)
- **Memory system** using FSRS algorithm for tracking concept strength
- **Temporal awareness** with a simulation clock
- **Belief and opinion management** with sentiment tracking
- **LLM client** for text generation (optional)

## Basic Usage

```python
from ghost_kg import GhostAgent, Rating
import datetime

# Create an agent
agent = GhostAgent("Alice", db_path="agent.db")

# Set simulation time
agent.set_time(datetime.datetime.now(datetime.timezone.utc))

# Learn a new triplet
agent.learn_triplet(
    source="I",
    relation="support",
    target="climate_action",
    rating=Rating.Good,
    sentiment=0.8
)

# Update memory strength
agent.update_memory("climate_action", Rating.Easy)

# Get agent's memories about a topic
memories = agent.get_memory_view("climate")
for concept, strength, relation in memories:
    print(f"{concept}: {strength:.2f} ({relation})")
```

## Architecture

```
GhostAgent
├── Knowledge Graph (NetworkX + SQLite)
├── Memory System (FSRS)
├── Simulation Clock (datetime)
└── LLM Client (Ollama, optional)
```

## API Reference

::: ghost_kg.agent.GhostAgent
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
