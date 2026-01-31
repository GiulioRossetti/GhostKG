# Storage API

The `KnowledgeDB` class provides database operations for storing and querying knowledge graphs in SQLite.

## Module Location

```python
# Recommended: Import from top-level package
from ghost_kg import KnowledgeDB, NodeState

# Also supported: Import from subpackage
from ghost_kg.storage import KnowledgeDB, NodeState
```

## Overview

KnowledgeDB handles:

- **Node management**: Store and update entities with memory states
- **Relation management**: Store connections between entities with metadata
- **Temporal queries**: Query knowledge at specific time points
- **Interaction logging**: Track agent interactions for audit trails
- **Memory state tracking**: Store FSRS memory parameters per node

## Database Schema

### Tables

- **nodes**: Entities with FSRS memory state
- **relations**: Edges connecting entities
- **interactions**: Log of agent actions

See [Database Schema](../DATABASE_SCHEMA.md) for complete details.

## Basic Usage

```python
from ghost_kg.storage import KnowledgeDB, NodeState
import datetime

# Initialize database
db = KnowledgeDB("knowledge.db")

# Store a node with memory state
now = datetime.datetime.now(datetime.timezone.utc)
state = NodeState(
    stability=5.0,
    difficulty=5.0,
    last_review=now,
    reps=1,
    state=2
)

db.upsert_node(
    owner_id="Alice",
    node_id="climate_change",
    state=state,
    timestamp=now
)

# Add a relation
db.add_relation(
    owner_id="Alice",
    source="I",
    relation="support",
    target="climate_action",
    sentiment=0.8,
    timestamp=now
)

# Query agent's stance on a topic
stance_results = db.get_agent_stance(
    owner_id="Alice",
    topic="climate",
    current_time=now
)

for row in stance_results:
    print(f"Relation: {row['relation']}, Target: {row['target']}")
```

## Performance

The database uses indexes for efficient queries:

- Owner-based queries: O(log n)
- Temporal queries: O(log n)
- Relation lookups: O(log n)

## API Reference

::: ghost_kg.storage.KnowledgeDB
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.storage.NodeState
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
