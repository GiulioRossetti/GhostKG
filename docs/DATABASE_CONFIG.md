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

## Connection Pool Configuration

GhostKG exposes connection pool settings for PostgreSQL and MySQL to optimize performance for your workload.

### Pool Parameters

| Parameter | Description | Default | Applies To |
|-----------|-------------|---------|------------|
| `pool_size` | Number of connections to keep in the pool | 5 | PostgreSQL, MySQL |
| `max_overflow` | Maximum additional connections beyond pool_size | 10 | PostgreSQL, MySQL |
| `pool_timeout` | Seconds to wait for a connection from the pool | 30 | PostgreSQL, MySQL |
| `pool_recycle` | Seconds before recycling connections | 3600 (MySQL only) | MySQL, PostgreSQL |

**Note**: Pool configuration does not apply to SQLite (uses StaticPool for `:memory:` or NullPool for file-based).

### Examples

#### PostgreSQL with Custom Pool

```python
from ghost_kg import GhostAgent

agent = GhostAgent(
    "Alice",
    db_path="postgresql://user:pass@localhost/ghostkg",
    pool_size=10,           # Keep 10 connections in pool
    max_overflow=20,        # Allow up to 20 additional connections
    pool_timeout=60.0,      # Wait up to 60 seconds for connection
)
```

#### MySQL with Connection Recycling

```python
from ghost_kg import GhostAgent

agent = GhostAgent(
    "Bob",
    db_path="mysql+pymysql://user:pass@localhost/ghostkg",
    pool_size=8,
    max_overflow=15,
    pool_recycle=1800,      # Recycle connections after 30 minutes
)
```

#### High-Concurrency Setup

For applications with many agents or concurrent access:

```python
from ghost_kg.storage.database import KnowledgeDB

db = KnowledgeDB(
    db_url="postgresql://user:pass@localhost/ghostkg",
    pool_size=20,           # Large pool for many concurrent agents
    max_overflow=30,
    pool_timeout=10.0,      # Quick timeout to avoid blocking
)
```

### When to Tune Pool Settings

- **Low concurrency** (1-5 agents): Use defaults
- **Medium concurrency** (5-20 agents): `pool_size=10`, `max_overflow=20`
- **High concurrency** (20+ agents): `pool_size=20+`, `max_overflow=30+`
- **Memory constrained**: Lower `pool_size` and `max_overflow`
- **Connection limit reached**: Lower `pool_size` + `max_overflow`

### Monitoring Pool Usage

To debug connection issues, enable SQL logging:

```python
db = KnowledgeDB(
    db_url="postgresql://...",
    echo=True,              # Log all SQL queries
    pool_size=5,
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

## Complete Setup Examples

### PostgreSQL Setup (Step-by-Step)

#### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Start PostgreSQL service
sudo service postgresql start  # Linux
brew services start postgresql # macOS
```

#### 2. Create Database and User

```bash
# Connect to PostgreSQL as postgres user
sudo -u postgres psql

# In psql prompt:
CREATE DATABASE ghostkg;
CREATE USER ghostkg_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ghostkg TO ghostkg_user;

# Grant schema permissions (PostgreSQL 15+)
\c ghostkg
GRANT ALL ON SCHEMA public TO ghostkg_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ghostkg_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ghostkg_user;

\q
```

#### 3. Test Connection

```bash
psql -h localhost -U ghostkg_user -d ghostkg
# Enter password when prompted
```

#### 4. Use in GhostKG

```python
from ghost_kg import GhostAgent

agent = GhostAgent(
    "Alice",
    db_path="postgresql://ghostkg_user:your_secure_password@localhost:5432/ghostkg",
    pool_size=10,
    max_overflow=20,
)

# Tables (kg_nodes, kg_edges, kg_logs) are created automatically
agent.learn_triplet("PostgreSQL", "is", "powerful", Rating.Good)
```

#### 5. Verify Tables

```bash
psql -h localhost -U ghostkg_user -d ghostkg

# In psql:
\dt  # List all tables
SELECT * FROM kg_nodes LIMIT 5;
```

### MySQL Setup (Step-by-Step)

#### 1. Install MySQL

```bash
# Ubuntu/Debian
sudo apt-get install mysql-server

# macOS
brew install mysql

# Start MySQL service
sudo service mysql start       # Linux
brew services start mysql      # macOS
```

#### 2. Secure Installation

```bash
# Run security script
sudo mysql_secure_installation

# Set root password and answer security questions
```

#### 3. Create Database and User

```bash
# Connect to MySQL as root
sudo mysql -u root -p

# In MySQL prompt:
CREATE DATABASE ghostkg CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ghostkg_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON ghostkg.* TO 'ghostkg_user'@'localhost';
FLUSH PRIVILEGES;

# Verify
SHOW DATABASES;
SELECT user, host FROM mysql.user WHERE user='ghostkg_user';

EXIT;
```

#### 4. Test Connection

```bash
mysql -h localhost -u ghostkg_user -p ghostkg
# Enter password when prompted
```

#### 5. Use in GhostKG

```python
from ghost_kg import GhostAgent

agent = GhostAgent(
    "Bob",
    db_path="mysql+pymysql://ghostkg_user:your_secure_password@localhost:3306/ghostkg",
    pool_size=8,
    pool_recycle=3600,  # Important for MySQL
)

# Tables (kg_nodes, kg_edges, kg_logs) are created automatically
agent.learn_triplet("MySQL", "is", "popular", Rating.Good)
```

#### 6. Verify Tables

```bash
mysql -h localhost -u ghostkg_user -p ghostkg

# In MySQL:
SHOW TABLES;
DESCRIBE kg_nodes;
SELECT * FROM kg_nodes LIMIT 5;
```

### Docker Setup (Quick Start)

#### PostgreSQL with Docker

```bash
# Start PostgreSQL container
docker run --name ghostkg-postgres \
  -e POSTGRES_DB=ghostkg \
  -e POSTGRES_USER=ghostkg_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  -d postgres:15

# Connection string
postgresql://ghostkg_user:secure_password@localhost:5432/ghostkg
```

#### MySQL with Docker

```bash
# Start MySQL container
docker run --name ghostkg-mysql \
  -e MYSQL_DATABASE=ghostkg \
  -e MYSQL_USER=ghostkg_user \
  -e MYSQL_PASSWORD=secure_password \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -p 3306:3306 \
  -d mysql:8

# Connection string
mysql+pymysql://ghostkg_user:secure_password@localhost:3306/ghostkg
```

### Cloud Database Examples

#### AWS RDS (PostgreSQL)

```python
from ghost_kg import GhostAgent

agent = GhostAgent(
    "CloudAgent",
    db_path="postgresql://username:password@mydb.xxxx.us-east-1.rds.amazonaws.com:5432/ghostkg",
    pool_size=15,
    max_overflow=25,
    pool_timeout=30,
)
```

#### Google Cloud SQL (MySQL)

```python
from ghost_kg import GhostAgent

agent = GhostAgent(
    "CloudAgent",
    db_path="mysql+pymysql://username:password@34.xxx.xxx.xxx:3306/ghostkg",
    pool_size=12,
    pool_recycle=1800,
)
```

#### Azure Database for PostgreSQL

```python
from ghost_kg import GhostAgent

agent = GhostAgent(
    "AzureAgent",
    db_path="postgresql://username@servername:password@servername.postgres.database.azure.com:5432/ghostkg?sslmode=require",
    pool_size=10,
)
```

## Troubleshooting Different DBMS

### PostgreSQL Issues

**Connection refused:**
```bash
# Check if PostgreSQL is running
sudo service postgresql status
sudo service postgresql start

# Check if listening on correct port
sudo netstat -plnt | grep 5432

# Edit postgresql.conf if needed
# Find with: sudo find / -name postgresql.conf
# Set: listen_addresses = '*'
```

**Authentication failed:**
```bash
# Edit pg_hba.conf to allow password authentication
# Find with: sudo find / -name pg_hba.conf
# Add line: host    all    all    127.0.0.1/32    md5
sudo service postgresql restart
```

### MySQL Issues

**Access denied:**
```bash
# Reset password if needed
sudo mysql
ALTER USER 'ghostkg_user'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

**Connection timeout:**
```bash
# Edit my.cnf to increase timeouts
# Find with: sudo find / -name my.cnf
# Add under [mysqld]:
# wait_timeout = 28800
# interactive_timeout = 28800
sudo service mysql restart
```

### General Issues

**"No module named psycopg2":**
```bash
pip install ghost_kg[postgres]
# or
pip install psycopg2-binary
```

**"No module named pymysql":**
```bash
pip install ghost_kg[mysql]
# or
pip install pymysql
```

**Tables not found:**
```python
# Explicitly create tables
from ghost_kg.storage.database import KnowledgeDB
db = KnowledgeDB(db_url="your_connection_string")
# Tables are created automatically on init
```

