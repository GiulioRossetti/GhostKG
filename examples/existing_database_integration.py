"""
Example: Using GhostKG with an Existing SQLite Database

This example demonstrates how GhostKG can be integrated into an application
that already uses a SQLite database. GhostKG will create its own tables
without affecting existing tables.
"""

import sys
import os
import sqlite3

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg import GhostAgent, Rating

# Path to an existing database (or will be created if doesn't exist)
DB_PATH = "my_application.db"

# Clean up from previous runs
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def setup_application_database():
    """
    Simulate an existing application that uses SQLite.
    
    This creates some application-specific tables and data.
    """
    print("=" * 70)
    print("STEP 1: Setting up existing application database")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create application-specific tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Add some sample data
    cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)",
                   ("alice", "alice@example.com"))
    cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)",
                   ("bob", "bob@example.com"))
    
    user_id = cursor.lastrowid
    cursor.execute("INSERT INTO documents (user_id, title, content) VALUES (?, ?, ?)",
                   (user_id, "My First Document", "This is some content about AI."))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Created application tables: users, documents")
    print(f"✓ Added sample data: 2 users, 1 document")
    print()


def integrate_ghostkg():
    """
    Add GhostKG to the existing application.
    
    GhostKG will create its own tables (nodes, edges, logs) in the same database.
    """
    print("=" * 70)
    print("STEP 2: Integrating GhostKG with existing database")
    print("=" * 70)
    
    # Create a GhostKG agent using the same database
    agent = GhostAgent("Alice", db_path=DB_PATH)
    print(f"✓ Created GhostAgent connected to {DB_PATH}")
    
    # Use GhostKG to add knowledge
    agent.learn_triplet("AI", "is", "transformative", Rating.Good)
    agent.learn_triplet("Machine Learning", "requires", "data", Rating.Easy)
    agent.learn_triplet("Python", "is used for", "AI development", Rating.Good)
    
    print(f"✓ GhostKG learned 3 triplets")
    print()


def verify_coexistence():
    """
    Verify that both application tables and GhostKG tables coexist.
    """
    print("=" * 70)
    print("STEP 3: Verifying table coexistence")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("All tables in the database:")
    for table in tables:
        print(f"  - {table}")
    
    # Verify application data is intact
    print("\nApplication data (users table):")
    cursor.execute("SELECT username, email FROM users")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    # Verify GhostKG data
    print("\nGhostKG data (edges table):")
    cursor.execute("SELECT source, relation, target FROM kg_edges LIMIT 5")
    for row in cursor.fetchall():
        print(f"  - {row[0]} --{row[1]}--> {row[2]}")
    
    conn.close()
    print()


def query_agent_knowledge():
    """
    Show how to query the agent's knowledge.
    """
    print("=" * 70)
    print("STEP 4: Querying agent knowledge")
    print("=" * 70)
    
    agent = GhostAgent("Alice", db_path=DB_PATH)
    
    # Get agent's view on a topic
    memory_view = agent.get_memory_view("AI")
    print("Alice's knowledge about AI:")
    print(memory_view)
    print()


def main():
    """Run the example."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Using GhostKG with an Existing SQLite Database")
    print("=" * 70)
    print()
    
    # Step 1: Create an application database
    setup_application_database()
    
    # Step 2: Integrate GhostKG
    integrate_ghostkg()
    
    # Step 3: Verify coexistence
    verify_coexistence()
    
    # Step 4: Query knowledge
    query_agent_knowledge()
    
    print("=" * 70)
    print("✅ SUCCESS!")
    print("=" * 70)
    print("\nKey takeaways:")
    print("  • GhostKG creates its tables (nodes, edges, logs) in the existing database")
    print("  • Application tables (users, documents) remain untouched")
    print("  • Both systems can work together in the same SQLite file")
    print("  • No conflicts or data loss occur")
    print(f"\nDatabase saved to: {DB_PATH}")
    print()


if __name__ == "__main__":
    main()
