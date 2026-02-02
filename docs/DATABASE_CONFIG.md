# Database Configuration Guide

## Overview

GhostKG supports multiple database backends through SQLAlchemy ORM:
- **SQLite** (default) - Embedded, file-based or in-memory
- **PostgreSQL** - Scalable, enterprise-grade RDBMS
- **MySQL** - Popular, cloud-friendly RDBMS

## Quick Start

### SQLite (Default)

No configuration needed! SQLite is built into Python:

```python
from ghost_kg import GhostAgent

# Uses agent_memory.db in current directory (created automatically)
agent = GhostAgent("Alice")

# Or specify a different path
agent = GhostAgent("Bob", db_path="custom.db")

# Or use in-memory database (no persistence)
agent = GhostAgent("Charlie", db_path=":memory:")
```

### PostgreSQL

1. **Install driver:**
   ```bash
   pip install ghost_kg[postgres]
   ```

2. **Create database:**
   ```sql
   CREATE DATABASE ghostkg;
   GRANT ALL PRIVILEGES ON DATABASE ghostkg TO your_user;
   ```

3. **Use in code:**
   ```python
   agent = GhostAgent(
       "Alice",
       db_path="postgresql://user:password@localhost:5432/ghostkg"
   )
   ```

### MySQL

1. **Install driver:**
   ```bash
   pip install ghost_kg[mysql]
   ```

2. **Create database:**
   ```sql
   CREATE DATABASE ghostkg CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   GRANT ALL PRIVILEGES ON ghostkg.* TO 'your_user'@'localhost';
   ```

3. **Use in code:**
   ```python
   agent = GhostAgent(
       "Alice",
       db_path="mysql+pymysql://user:password@localhost:3306/ghostkg"
   )
   ```

## Connection String Formats

### SQLite

```
# File-based (relative path)
sqlite:///agent_memory.db

# File-based (absolute path)
sqlite:////absolute/path/to/database.db

# In-memory (not persisted)
sqlite:///:memory:

# Legacy format (auto-converted to SQLite URL)
agent_memory.db
```

### PostgreSQL

```
postgresql://username:password@hostname:port/database_name

# With specific options
postgresql://user:pass@localhost:5432/ghostkg?connect_timeout=10

# Using psycopg2 driver explicitly
postgresql+psycopg2://user:pass@localhost/ghostkg
```

### MySQL

```
mysql+pymysql://username:password@hostname:port/database_name

# With specific options
mysql+pymysql://user:pass@localhost:3306/ghostkg?charset=utf8mb4

# Alternative drivers
mysql+mysqlconnector://user:pass@localhost/ghostkg
```

## Environment Variables

Store sensitive connection information in environment variables:

```bash
# .env file
export GHOSTKG_DB_URL="postgresql://user:password@localhost/ghostkg"
```

```python
import os
from ghost_kg import GhostAgent

db_url = os.getenv("GHOSTKG_DB_URL", "sqlite:///agent_memory.db")
agent = GhostAgent("Alice", db_path=db_url)
```

## Configuration Options

### Enable SQL Query Logging

For debugging, enable SQL query logging:

```python
from ghost_kg.storage.database import KnowledgeDB

db = KnowledgeDB(
    db_path="postgresql://...",
    echo=True  # Prints all SQL queries to console
)
```

### Connection Pooling

Connection pooling is automatically configured based on database type:

| Database | Pool Type | Settings |
|----------|-----------|----------|
| SQLite (file) | NullPool | No pooling |
| SQLite (memory) | StaticPool | Single connection |
| PostgreSQL | QueuePool | 5 connections, overflow 10 |
| MySQL | QueuePool | 5 connections, overflow 10, 1h recycle |

To customize (advanced):

```python
from ghost_kg.storage.engine import DatabaseManager

manager = DatabaseManager(db_url="postgresql://...")
# Access manager.engine to configure pooling
```

## Database-Specific Considerations

### SQLite

**Pros:**
- No setup required
- Fast for single-user scenarios
- Perfect for development and testing
- Portable database files

**Cons:**
- Not suitable for concurrent writes
- Limited scalability
- Single server only

**Best for:**
- Development
- Single-agent simulations
- Embedded applications
- Small-scale deployments

### PostgreSQL

**Pros:**
- Excellent concurrency support
- Powerful features (JSON, full-text search)
- Battle-tested reliability
- Great for production

**Cons:**
- Requires separate server
- More complex setup
- Higher resource usage

**Best for:**
- Production deployments
- Multi-agent simulations
- Concurrent access scenarios
- Large-scale applications

### MySQL

**Pros:**
- Widely available
- Good cloud support (AWS RDS, Google Cloud SQL)
- Easy replication
- Familiar to many developers

**Cons:**
- Requires separate server
- Some feature limitations vs PostgreSQL

**Best for:**
- Cloud deployments
- Shared hosting environments
- MySQL-centric infrastructure
- Multi-region deployments

## Performance Tips

### SQLite

```python
# Use file-based for persistence
agent = GhostAgent("Alice", db_path="agent_memory.db")

# Use in-memory for speed (no persistence)
agent = GhostAgent("Bob", db_path=":memory:")
```

### PostgreSQL

```sql
-- Create indexes for better performance (done automatically)
CREATE INDEX idx_edges_owner_source ON edges(owner_id, source);
CREATE INDEX idx_edges_owner_target ON edges(owner_id, target);
CREATE INDEX idx_nodes_last_review ON nodes(owner_id, last_review DESC);

-- Enable query statistics
ALTER DATABASE ghostkg SET log_statement = 'all';
```

### MySQL

```sql
-- Use InnoDB engine (default in MySQL 5.5+)
ALTER TABLE nodes ENGINE=InnoDB;
ALTER TABLE edges ENGINE=InnoDB;
ALTER TABLE logs ENGINE=InnoDB;

-- Optimize tables periodically
OPTIMIZE TABLE nodes, edges, logs;
```

## Security Best Practices

1. **Never hardcode credentials:**
   ```python
   # ❌ Bad
   agent = GhostAgent("Alice", db_path="postgresql://user:password@host/db")
   
   # ✅ Good
   import os
   db_url = os.getenv("GHOSTKG_DB_URL")
   agent = GhostAgent("Alice", db_path=db_url)
   ```

2. **Use SSL connections for remote databases:**
   ```python
   # PostgreSQL with SSL
   db_url = "postgresql://user:pass@host/db?sslmode=require"
   
   # MySQL with SSL
   db_url = "mysql+pymysql://user:pass@host/db?ssl_ca=/path/to/ca.pem"
   ```

3. **Restrict database user permissions:**
   ```sql
   -- PostgreSQL
   GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO ghostkg_user;
   
   -- MySQL
   GRANT SELECT, INSERT, UPDATE ON ghostkg.* TO 'ghostkg_user'@'localhost';
   ```

4. **Use separate databases for development and production:**
   ```python
   import os
   
   if os.getenv("ENV") == "production":
       db_url = os.getenv("PROD_DB_URL")
   else:
       db_url = "sqlite:///dev.db"
   
   agent = GhostAgent("Alice", db_path=db_url)
   ```

## Troubleshooting

### SQLite: "database is locked"

```python
# Issue: Concurrent access to SQLite
# Solution: Use PostgreSQL or MySQL for concurrent scenarios
# Or: Increase timeout
import sqlite3
sqlite3.connect("agent_memory.db", timeout=10.0)
```

### PostgreSQL: "FATAL: database does not exist"

```bash
# Solution: Create the database first
createdb ghostkg

# Or
psql -c "CREATE DATABASE ghostkg;"
```

### MySQL: "Access denied for user"

```bash
# Solution: Grant permissions
mysql -u root -p
GRANT ALL PRIVILEGES ON ghostkg.* TO 'user'@'localhost' IDENTIFIED BY 'password';
FLUSH PRIVILEGES;
```

### Any: "No module named 'psycopg2' or 'pymysql'"

```bash
# Solution: Install database drivers
pip install ghost_kg[postgres]  # For PostgreSQL
pip install ghost_kg[mysql]     # For MySQL
pip install ghost_kg[database]  # For all drivers
```

## Migration Between Databases

Currently, GhostKG does not provide automatic migration between database types. To migrate:

### Option 1: Export/Import (Simple)

```python
# 1. Export from SQLite
from ghost_kg import GhostAgent

agent_old = GhostAgent("Alice", db_path="old.db")
# ... extract data using agent methods ...

# 2. Import to PostgreSQL
agent_new = GhostAgent("Alice", db_path="postgresql://...")
# ... recreate data using agent methods ...
```

### Option 2: Direct SQL (Advanced)

Use database-specific tools to export/import:

```bash
# SQLite to SQL dump
sqlite3 old.db .dump > dump.sql

# Modify dump.sql for PostgreSQL/MySQL syntax
# Import to new database
psql ghostkg < dump.sql  # PostgreSQL
mysql ghostkg < dump.sql # MySQL
```

## Next Steps

- See [Multi-Database Demo](../examples/multi_database_demo.py) for working examples
- Check [API Documentation](API.md) for database methods
- Read [Database Schema](DATABASE_SCHEMA.md) for table structures
