# Using GhostKG with an Existing SQLite Database

This example demonstrates how to integrate GhostKG into an application that already uses a SQLite database.

## Overview

**GhostKG is designed to work seamlessly with existing SQLite databases.** You can use it alongside your existing application tables without any conflicts or data loss.

## Use Case

Imagine you have an application with its own SQLite database containing user data, documents, or other information. You want to add AI agent capabilities with knowledge graphs, but you don't want to:
- Create a separate database file
- Migrate your existing data
- Risk conflicts between systems

GhostKG solves this by:
1. Using `CREATE TABLE IF NOT EXISTS` for all its tables
2. Using `CREATE INDEX IF NOT EXISTS` for all indexes
3. Automatically migrating schema when needed (adding missing columns)
4. Never touching tables that aren't its own

## Step-by-Step Walkthrough

### 1. Existing Application Setup

Your application already has a database with its own tables:

```python
import sqlite3

DB_PATH = "my_application.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create your application tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        title TEXT NOT NULL,
        content TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

conn.commit()
conn.close()
```

### 2. Integrate GhostKG

Simply create a GhostKG agent pointing to your existing database:

```python
from ghost_kg import GhostAgent, Rating

# Use the same database path
agent = GhostAgent("MyAgent", db_path="my_application.db")

# GhostKG creates its tables (nodes, edges, logs) if they don't exist
# Your existing tables remain completely untouched
agent.learn_triplet("Python", "is", "great", Rating.Good)
```

### 3. Verify Coexistence

Both systems work together in the same database:

```python
import sqlite3

conn = sqlite3.connect("my_application.db")
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print("All tables:", tables)
# Output: ['users', 'documents', 'nodes', 'edges', 'logs', ...]

# Query application data - still intact!
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

# Query GhostKG data
cursor.execute("SELECT source, relation, target FROM edges")
triplets = cursor.fetchall()

conn.close()
```

## What GhostKG Creates

When you connect to a database, GhostKG creates these tables (if they don't exist):

| Table | Purpose | Conflicts? |
|-------|---------|-----------|
| **nodes** | Knowledge graph entities with FSRS memory state | ❌ Only if you have a table named "nodes" |
| **edges** | Relationships (triplets) between entities | ❌ Only if you have a table named "edges" |
| **logs** | Agent interaction history | ❌ Only if you have a table named "logs" |

**Plus indexes** for performance: `idx_edges_owner_source`, `idx_edges_owner_target`, `idx_edges_created`, `idx_nodes_last_review`, `idx_nodes_owner`, `idx_logs_agent_time`, `idx_logs_action`

## Safety Guarantees

✅ **Your data is safe**:
- GhostKG only creates tables if they don't exist (`CREATE TABLE IF NOT EXISTS`)
- Existing tables are never modified or deleted
- Foreign key constraints are respected
- Transactions ensure data consistency

✅ **No naming conflicts**:
- Unless you already have tables named `nodes`, `edges`, or `logs`, there will be no conflicts
- If you do have these tables with different schemas, GhostKG will try to use them (this may cause errors)

✅ **Schema migration**:
- If GhostKG tables exist but are missing columns (e.g., from an older version), GhostKG automatically adds them using `ALTER TABLE`

## Running the Example

```bash
cd examples
python existing_database_integration.py
```

### Expected Output

```
======================================================================
EXAMPLE: Using GhostKG with an Existing SQLite Database
======================================================================

STEP 1: Setting up existing application database
✓ Created application tables: users, documents
✓ Added sample data: 2 users, 1 document

STEP 2: Integrating GhostKG with existing database
✓ Created GhostAgent connected to my_application.db
✓ GhostKG learned 3 triplets

STEP 3: Verifying table coexistence
All tables in the database:
  - documents
  - edges
  - logs
  - nodes
  - users

Application data (users table):
  - alice: alice@example.com
  - bob: bob@example.com

GhostKG data (edges table):
  - ai --is--> transformative
  - machine learning --requires--> data
  - python --is used for--> ai development

✅ SUCCESS!
```

## Best Practices

1. **Use unique table names**: If possible, avoid naming your tables `nodes`, `edges`, or `logs`
2. **Backup first**: Always backup your database before integrating new libraries
3. **Test in development**: Test GhostKG integration with a copy of your database first
4. **Monitor database size**: Knowledge graphs can grow large; monitor disk space
5. **Use separate databases for critical data**: If your application data is mission-critical, consider using a separate database file for GhostKG

## Common Questions

**Q: What if my database already has a table named "nodes"?**  
A: GhostKG will try to use it. If the schema doesn't match, you'll get errors. In this case, use a separate database or rename your existing table.

**Q: Can multiple agents share the same database?**  
A: Yes! Agents are identified by `owner_id` in the tables, so multiple agents can safely coexist in the same database.

**Q: What if the database file doesn't exist?**  
A: SQLite automatically creates it. GhostKG then creates its tables in the new file.

**Q: Does GhostKG modify SQLite settings or pragmas?**  
A: No. GhostKG uses the default SQLite configuration with `check_same_thread=False` for multi-threaded access.

## Related Documentation

- [Database Schema](../DATABASE_SCHEMA.md) - Complete schema documentation
- [Core Components](../CORE_COMPONENTS.md) - GhostAgent and KnowledgeDB API
- [External Program Example](external_program.md) - Using GhostKG as a library
