# GhostKG Database Schema

This document describes the database schema used by GhostKG for storing knowledge graphs and memory states.

## Overview

GhostKG uses SQLite for persistence, with three main tables:
- **nodes**: Entities in the knowledge graph with FSRS memory states
- **edges**: Relationships (triplets) between entities with sentiment
- **logs**: Interaction history for debugging and analysis

## Database Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SQLite Database                       │
│                                                          │
│  ┌────────────────────┐                                │
│  │      nodes         │◄───┐                           │
│  │  (Entities/KG)     │    │                           │
│  └────────────────────┘    │  Foreign Keys             │
│           ▲                 │                           │
│           │                 │                           │
│           │                 │                           │
│  ┌────────────────────┐    │                           │
│  │      edges         │────┘                           │
│  │   (Triplets)       │                                │
│  └────────────────────┘                                │
│                                                          │
│  ┌────────────────────┐                                │
│  │       logs         │                                │
│  │   (History)        │                                │
│  └────────────────────┘                                │
└─────────────────────────────────────────────────────────┘
```

## Table Schemas

### nodes Table

Stores entities (concepts, people, topics) with their FSRS memory states.

#### Schema

```sql
CREATE TABLE IF NOT EXISTS nodes (
    owner_id TEXT,              -- Agent who owns this node
    id TEXT,                    -- Node identifier (entity name)
    stability REAL DEFAULT 0,   -- FSRS stability (days)
    difficulty REAL DEFAULT 0,  -- FSRS difficulty (1-10)
    last_review TIMESTAMP,      -- Last time this node was reviewed
    reps INTEGER DEFAULT 0,     -- Number of repetitions
    state INTEGER DEFAULT 0,    -- FSRS state (0=new, 1=learning, 2=review)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sim_day INTEGER,            -- Round-based time: day number (>= 1)
    sim_hour INTEGER,           -- Round-based time: hour (0-23)
    PRIMARY KEY (owner_id, id)
)
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| owner_id | TEXT | Primary Key | Agent name who owns this node |
| id | TEXT | Primary Key | Entity name (e.g., "climate change", "Bob", "I") |
| stability | REAL | DEFAULT 0 | FSRS stability in days (how long until R=0.9) |
| difficulty | REAL | DEFAULT 0 | FSRS difficulty rating (1-10 scale) |
| last_review | TIMESTAMP | NULL | When this entity was last accessed |
| reps | INTEGER | DEFAULT 0 | Number of times reviewed/reinforced |
| state | INTEGER | DEFAULT 0 | FSRS state: 0=new, 1=learning, 2=review |
| created_at | TIMESTAMP | DEFAULT NOW | When entity was first added |
| sim_day | INTEGER | NULL | Round-based time: day number (>= 1) |
| sim_hour | INTEGER | NULL | Round-based time: hour (0-23) |

**Note on Time Columns**: 
- `created_at`/`last_review`: Used for datetime-based simulations
- `sim_day`/`sim_hour`: Used for round-based simulations (e.g., game turns)
- Both can coexist, or only one set may be populated depending on simulation mode

#### Indexes

```sql
-- Primary key automatically creates index on (owner_id, id)
CREATE INDEX idx_nodes_owner ON nodes(owner_id);
CREATE INDEX idx_nodes_last_review ON nodes(owner_id, last_review);
```

#### Example Data

```
owner_id | id              | stability | difficulty | last_review         | reps | state | created_at
---------|-----------------|-----------|------------|---------------------|------|-------|------------
Alice    | I               | 10.5      | 4.5        | 2025-01-01 10:00:00 | 3    | 2     | 2025-01-01 09:00:00
Alice    | climate change  | 5.2       | 6.8        | 2025-01-01 09:30:00 | 1    | 1     | 2025-01-01 09:00:00
Alice    | Bob             | 2.4       | 5.0        | 2025-01-01 09:00:00 | 1    | 1     | 2025-01-01 09:00:00
Bob      | I               | 15.3      | 3.2        | 2025-01-01 10:30:00 | 5    | 2     | 2025-01-01 09:00:00
```

### edges Table

Stores relationships (triplets) between entities, forming the knowledge graph.

#### Schema

```sql
CREATE TABLE IF NOT EXISTS edges (
    owner_id TEXT,              -- Agent who owns this edge
    source TEXT,                -- Subject entity
    target TEXT,                -- Object entity
    relation TEXT,              -- Relationship type
    weight REAL DEFAULT 1.0,    -- Connection strength
    sentiment REAL DEFAULT 0.0, -- Emotional valence (-1.0 to 1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sim_day INTEGER,            -- Round-based time: day number (>= 1)
    sim_hour INTEGER,           -- Round-based time: hour (0-23)
    PRIMARY KEY (owner_id, source, target, relation),
    FOREIGN KEY(owner_id, source) REFERENCES nodes(owner_id, id),
    FOREIGN KEY(owner_id, target) REFERENCES nodes(owner_id, id)
)
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| owner_id | TEXT | Primary Key, FK | Agent name who owns this edge |
| source | TEXT | Primary Key, FK | Subject entity (e.g., "I", "Bob", "UBI") |
| target | TEXT | Primary Key, FK | Object entity (e.g., "renewable energy", "jobs") |
| relation | TEXT | Primary Key | Relationship verb (e.g., "supports", "affects") |
| weight | REAL | DEFAULT 1.0 | Connection strength (unused currently) |
| sentiment | REAL | DEFAULT 0.0 | Emotional valence: -1.0 (negative) to 1.0 (positive) |
| created_at | TIMESTAMP | DEFAULT NOW | When relationship was established |
| sim_day | INTEGER | NULL | Round-based time: day number (>= 1) |
| sim_hour | INTEGER | NULL | Round-based time: hour (0-23) |

#### Indexes

```sql
-- Primary key automatically creates index on (owner_id, source, target, relation)
CREATE INDEX idx_edges_owner_source ON edges(owner_id, source);
CREATE INDEX idx_edges_owner_target ON edges(owner_id, target);
CREATE INDEX idx_edges_created ON edges(owner_id, created_at);
```

#### Example Data

```
owner_id | source | target          | relation   | weight | sentiment | created_at
---------|--------|-----------------|------------|--------|-----------|------------
Alice    | I      | renewable energy| support    | 1.0    | 0.8       | 2025-01-01 09:00:00
Alice    | I      | climate change  | care_about | 1.0    | 0.9       | 2025-01-01 09:00:00
Alice    | Bob    | carbon tax      | supports   | 1.0    | 0.6       | 2025-01-01 09:30:00
Bob      | I      | economy         | prioritize | 1.0    | 0.7       | 2025-01-01 09:00:00
```

### logs Table

Stores interaction history for debugging, analysis, and replay.

#### Schema

```sql
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT,            -- Agent who performed the action
    action_type TEXT,           -- Type of action (READ/WRITE)
    content TEXT,               -- Text content of the interaction
    content_uuid TEXT,          -- UUID when content is not stored
    annotations JSON,           -- Metadata in JSON format
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sim_day INTEGER,            -- Round-based time: day number (>= 1)
    sim_hour INTEGER            -- Round-based time: hour (0-23)
)
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | INTEGER | Primary Key, Auto | Unique log entry ID |
| agent_name | TEXT | NOT NULL | Agent name |
| action_type | TEXT | NOT NULL | "READ" (absorbing) or "WRITE" (generating) |
| content | TEXT | NULL | The actual text content |
| content_uuid | TEXT | NULL | UUID when content is not stored |
| annotations | JSON | NULL | Metadata: context_used, triplets_count, mode, etc. |
| timestamp | TIMESTAMP | DEFAULT NOW | When action occurred |
| sim_day | INTEGER | NULL | Round-based time: day number (>= 1) |
| sim_hour | INTEGER | NULL | Round-based time: hour (0-23) |

#### Indexes

```sql
CREATE INDEX idx_logs_agent ON logs(agent_name);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_action ON logs(action_type);
```

#### Annotations Format

The `annotations` column stores JSON with metadata about the interaction:

**For READ actions:**
```json
{
    "author": "Bob",
    "triplets_count": 3,
    "external": true,
    "mode": "FAST",
    "sentiment": 0.5,
    "entities": ["climate change", "renewable energy"]
}
```

**For WRITE actions:**
```json
{
    "triplets_count": 2,
    "external": true,
    "context_used": "MY CURRENT STANCE: I support renewable energy..."
}
```

#### Example Data

```
id | agent_name | action_type | content                      | annotations                           | timestamp
---|------------|-------------|------------------------------|---------------------------------------|------------
1  | Alice      | READ        | Bob supports carbon tax      | {"author":"Bob","triplets_count":2}  | 2025-01-01 09:00:00
2  | Alice      | WRITE       | I agree with that approach   | {"context_used":"...","external":true}| 2025-01-01 09:05:00
3  | Bob        | READ        | Alice mentioned renewable... | {"author":"Alice","mode":"FAST"}     | 2025-01-01 09:10:00
```

## Relationships

### Entity-Relationship Diagram

```
┌─────────────────┐
│     nodes       │
│  ┌───────────┐  │
│  │ owner_id  │◄─┼───────────────┐
│  │ id        │  │               │
│  │ stability │  │               │
│  │ difficulty│  │               │
│  │ ...       │  │               │
│  └───────────┘  │               │
└─────────────────┘               │
         ▲                         │
         │ FK                      │
         │                         │
┌─────────────────┐                │
│     edges       │                │
│  ┌───────────┐  │                │
│  │ owner_id  │──┼────────────────┘
│  │ source    │──┼──(FK to nodes.id)
│  │ target    │──┼──(FK to nodes.id)
│  │ relation  │  │
│  │ sentiment │  │
│  │ ...       │  │
│  └───────────┘  │
└─────────────────┘

┌─────────────────┐
│     logs        │
│  ┌───────────┐  │
│  │ id        │  │
│  │agent_name │  │  (No FK - independent)
│  │action_type│  │
│  │ content   │  │
│  │annotations│  │
│  └───────────┘  │
└─────────────────┘
```

### Foreign Key Constraints

1. **edges.source** → **nodes.id** (via owner_id)
2. **edges.target** → **nodes.id** (via owner_id)

When inserting an edge, both source and target nodes must exist. The `upsert_node` operation is called automatically by `add_relation` to ensure nodes exist.

## Query Patterns

### Common Queries

#### 1. Get Agent's Stance on Topic

```sql
SELECT source, relation, target, sentiment 
FROM edges
WHERE owner_id = 'Alice'
  AND (source = 'I' OR source = 'Alice')
  AND (
    target LIKE '%climate%'
    OR created_at >= datetime('2025-01-01 09:00:00', '-60 minutes')
  )
ORDER BY created_at DESC
LIMIT 8;
```

**Use**: Retrieve what the agent believes about a topic.

#### 2. Get World Knowledge

```sql
SELECT source, relation, target
FROM edges
WHERE owner_id = 'Alice'
  AND source != 'I'
  AND source != 'Alice'
  AND (source LIKE '%climate%' OR target LIKE '%climate%')
ORDER BY created_at DESC
LIMIT 10;
```

**Use**: Retrieve general facts the agent knows (not personal beliefs).

#### 3. Get Agent's Memory State

```sql
SELECT n.id, n.stability, n.difficulty, n.reps, n.state,
       (julianday('now') - julianday(n.last_review)) as days_since_review
FROM nodes n
WHERE n.owner_id = 'Alice'
  AND n.id IN (
    SELECT DISTINCT target FROM edges WHERE owner_id = 'Alice' AND source = 'I'
  )
ORDER BY n.last_review DESC;
```

**Use**: See what the agent remembers and how well.

#### 4. Get Interaction History

```sql
SELECT action_type, content, annotations, timestamp
FROM logs
WHERE agent_name = 'Alice'
ORDER BY timestamp DESC
LIMIT 20;
```

**Use**: Debug agent behavior or replay conversations.

#### 5. Find Connected Entities

```sql
SELECT DISTINCT e2.target
FROM edges e1
JOIN edges e2 ON e1.owner_id = e2.owner_id AND e1.target = e2.source
WHERE e1.owner_id = 'Alice'
  AND e1.source = 'climate change'
ORDER BY e2.created_at DESC;
```

**Use**: Find what's related to a concept (2-hop traversal).

## Data Integrity

### Constraints

1. **Primary Keys**: Ensure uniqueness
   - nodes: (owner_id, id)
   - edges: (owner_id, source, target, relation)
   - logs: (id)

2. **Foreign Keys**: Ensure referential integrity
   - edges.source → nodes.id
   - edges.target → nodes.id

3. **Defaults**: Provide sensible initial values
   - stability, difficulty, reps, state
   - weight, sentiment
   - timestamps

### Triggers (Not Implemented)

Potential future triggers:

```sql
-- Auto-update node.last_review when edge is created
CREATE TRIGGER update_node_review 
AFTER INSERT ON edges
BEGIN
  UPDATE nodes 
  SET last_review = NEW.created_at
  WHERE owner_id = NEW.owner_id 
    AND (id = NEW.source OR id = NEW.target);
END;
```

## Performance Considerations

### Index Usage

Query performance depends on proper index usage:

1. **Primary Key Lookups**: O(log n)
   - `WHERE owner_id = ? AND id = ?`

2. **Owner Scans**: O(k) where k = number of records for owner
   - `WHERE owner_id = ?`

3. **Time-Range Queries**: O(log n + k)
   - `WHERE owner_id = ? AND created_at >= ?`

4. **Full Text Search**: O(n) (slow)
   - `WHERE target LIKE '%keyword%'`

### Optimization Strategies

1. **Limit Results**: Always use LIMIT in queries
2. **Index on (owner_id, created_at)**: Fast time-based filtering
3. **Batch Operations**: Use transactions for multiple inserts
4. **Prepared Statements**: Faster execution, prevents SQL injection

### Storage Estimates

| Entity | Size per Record | 1000 Records | 100k Records |
|--------|----------------|--------------|--------------|
| Node | ~100 bytes | ~100 KB | ~10 MB |
| Edge | ~150 bytes | ~150 KB | ~15 MB |
| Log | ~500 bytes | ~500 KB | ~50 MB |

**Example**:
- 10 agents
- 100 triplets per agent (1000 total)
- 50 nodes per agent (500 total)
- 100 log entries per agent (1000 total)

**Total**: ~750 KB

## Backup and Migration

### Backup

```bash
# Simple file copy
cp agent_memory.db agent_memory.backup.db

# SQLite dump
sqlite3 agent_memory.db .dump > backup.sql

# Restore from dump
sqlite3 new_db.db < backup.sql
```

### Migration

For schema changes, create migration scripts:

```python
import sqlite3

def migrate_v1_to_v2(db_path):
    conn = sqlite3.connect(db_path)
    
    # Example: Add new column
    conn.execute("ALTER TABLE nodes ADD COLUMN version INTEGER DEFAULT 1")
    
    conn.commit()
    conn.close()
```

## Schema Versioning

Current version: **1.0**

Changes should be tracked in migration files:
- `migrations/001_initial_schema.sql`
- `migrations/002_add_sentiment.sql`
- etc.

## Security Considerations

### SQL Injection Prevention

Always use parameterized queries:

```python
# ✅ Safe
cursor.execute("SELECT * FROM nodes WHERE owner_id = ?", (agent_name,))

# ❌ Unsafe
cursor.execute(f"SELECT * FROM nodes WHERE owner_id = '{agent_name}'")
```

### Access Control

Currently no built-in access control. Recommendations:

1. Use separate database files for different applications
2. Set file permissions: `chmod 600 agent_memory.db`
3. Implement application-level authentication
4. Use read-only connections when possible

## Monitoring

### Database Statistics

```sql
-- Table sizes
SELECT 
    name as table_name,
    COUNT(*) as row_count
FROM sqlite_master sm
JOIN (
    SELECT 'nodes' as name UNION
    SELECT 'edges' UNION
    SELECT 'logs'
) t ON sm.name = t.name
GROUP BY sm.name;

-- Database file size
SELECT page_count * page_size as size_bytes
FROM pragma_page_count(), pragma_page_size();
```

### Health Checks

```python
def check_db_health(db_path):
    conn = sqlite3.connect(db_path)
    
    # Check integrity
    result = conn.execute("PRAGMA integrity_check").fetchone()
    assert result[0] == "ok"
    
    # Check orphaned edges
    orphaned = conn.execute("""
        SELECT COUNT(*) FROM edges e
        WHERE NOT EXISTS (
            SELECT 1 FROM nodes n 
            WHERE n.owner_id = e.owner_id AND n.id = e.source
        )
    """).fetchone()[0]
    
    assert orphaned == 0, f"Found {orphaned} orphaned edges"
    
    conn.close()
```

## Conclusion

The GhostKG database schema is designed for:
- **Simplicity**: Three tables, clear relationships
- **Efficiency**: Proper indexes for common queries
- **Flexibility**: JSON annotations for extensibility
- **Integrity**: Foreign keys and constraints
- **Debuggability**: Comprehensive logging

The schema supports the core features of GhostKG while remaining easy to understand and maintain.
