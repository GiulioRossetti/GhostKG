"""
Example: Using GhostKG with Multiple Database Backends

Demonstrates SQLite, PostgreSQL, and MySQL support.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg import GhostAgent, Rating
import tempfile


def demo_sqlite():
    """Demonstrate SQLite support (default)."""
    print("\n" + "="*70)
    print("DEMO 1: SQLite Database (Default)")
    print("="*70)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        print(f"\n1. Using file path (legacy mode): {db_path}")
        agent = GhostAgent("Alice", db_path=db_path)
        agent.learn_triplet("Python", "is", "awesome", Rating.Good)
        print("✓ Agent created with SQLite database")
        
        # Verify
        memory = agent.get_memory_view("Python")
        print(f"✓ Memory retrieved: {memory[:50]}...")
        
        # Cleanup
        os.unlink(db_path)
        
        print("\n2. Using SQLite URL:")
        agent2 = GhostAgent("Bob", db_path=":memory:")
        agent2.learn_triplet("AI", "requires", "data", Rating.Easy)
        print("✓ Agent created with in-memory SQLite")
        
        print("\n✅ SQLite demo complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)


def demo_postgresql():
    """Demonstrate PostgreSQL support."""
    print("\n" + "="*70)
    print("DEMO 2: PostgreSQL Database")
    print("="*70)
    
    # Example connection string (would need actual PostgreSQL server)
    db_url = os.environ.get("POSTGRES_URL")
    
    if not db_url:
        print("\n⊘ Skipping - Set POSTGRES_URL environment variable to test")
        print("   Example: export POSTGRES_URL='postgresql://user:pass@localhost/ghostkg'")
        return
    
    try:
        print(f"\n1. Connecting to PostgreSQL...")
        # Note: This would require the database to exist
        # GhostKG creates tables but not the database itself
        agent = GhostAgent("Alice", db_path=db_url)
        agent.learn_triplet("PostgreSQL", "is", "scalable", Rating.Good)
        print("✓ Agent created with PostgreSQL database")
        
        memory = agent.get_memory_view("PostgreSQL")
        print(f"✓ Memory retrieved: {memory[:50]}...")
        
        print("\n✅ PostgreSQL demo complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure:")
        print("   - PostgreSQL server is running")
        print("   - Database exists (CREATE DATABASE ghostkg;)")
        print("   - User has permissions")
        print("   - psycopg2-binary is installed (pip install ghost_kg[postgres])")


def demo_mysql():
    """Demonstrate MySQL support."""
    print("\n" + "="*70)
    print("DEMO 3: MySQL Database")
    print("="*70)
    
    # Example connection string (would need actual MySQL server)
    db_url = os.environ.get("MYSQL_URL")
    
    if not db_url:
        print("\n⊘ Skipping - Set MYSQL_URL environment variable to test")
        print("   Example: export MYSQL_URL='mysql+pymysql://user:pass@localhost/ghostkg'")
        return
    
    try:
        print(f"\n1. Connecting to MySQL...")
        # Note: This would require the database to exist
        agent = GhostAgent("Alice", db_path=db_url)
        agent.learn_triplet("MySQL", "is", "popular", Rating.Good)
        print("✓ Agent created with MySQL database")
        
        memory = agent.get_memory_view("MySQL")
        print(f"✓ Memory retrieved: {memory[:50]}...")
        
        print("\n✅ MySQL demo complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure:")
        print("   - MySQL server is running")
        print("   - Database exists (CREATE DATABASE ghostkg;)")
        print("   - User has permissions")
        print("   - PyMySQL is installed (pip install ghost_kg[mysql])")


def demo_multi_database():
    demo_pool_configuration()
    """Demonstrate using multiple databases simultaneously."""
    print("\n" + "="*70)
    print("DEMO 4: Multiple Databases Simultaneously")
    print("="*70)
    
    try:
        print("\n1. Creating agents with different databases...")
        
        # Agent 1: SQLite
        agent_sqlite = GhostAgent("Agent_SQLite", db_path=":memory:")
        agent_sqlite.learn_triplet("SQLite", "is", "embedded", Rating.Good)
        print("✓ Agent_SQLite using SQLite")
        
        # Agent 2: Another SQLite (different file)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path2 = tmp.name
        agent_sqlite2 = GhostAgent("Agent_SQLite2", db_path=db_path2)
        agent_sqlite2.learn_triplet("Data", "is", "important", Rating.Easy)
        print("✓ Agent_SQLite2 using different SQLite")
        
        print("\n2. Both agents work independently:")
        print(f"   Agent_SQLite: {agent_sqlite.get_memory_view('SQLite')[:40]}...")
        print(f"   Agent_SQLite2: {agent_sqlite2.get_memory_view('Data')[:40]}...")
        
        # Cleanup
        os.unlink(db_path2)
        
        print("\n✅ Multi-database demo complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")



def demo_pool_configuration():
    """Demonstrate connection pool configuration."""
    print("\n" + "="*70)
    print("DEMO 5: Connection Pool Configuration")
    print("="*70)
    
    print("\n1. Default pool settings (PostgreSQL simulation):")
    print("   agent = GhostAgent('name', db_path='postgresql://...')")
    print("   Default: pool_size=5, max_overflow=10")
    
    print("\n2. Custom pool settings (High Concurrency):")
    agent_config = """
    agent = GhostAgent(
        'HighConcurrency',
        db_path='postgresql://user:pass@localhost/ghostkg',
        pool_size=20,           # 20 connections in pool
        max_overflow=30,        # Up to 30 additional connections
        pool_timeout=60.0,      # 60 second timeout
    )
    """
    print(agent_config)
    print("   ✓ Suitable for 20+ concurrent agents")
    
    print("\n3. MySQL with connection recycling:")
    mysql_config = """
    agent = GhostAgent(
        'MySQLAgent',
        db_path='mysql+pymysql://user:pass@localhost/ghostkg',
        pool_size=8,
        pool_recycle=1800,      # Recycle after 30 minutes
    )
    """
    print(mysql_config)
    print("   ✓ Prevents stale MySQL connections")
    
    print("\n4. Memory-constrained environment:")
    low_mem_config = """
    agent = GhostAgent(
        'LowMemory',
        db_path='postgresql://user:pass@localhost/ghostkg',
        pool_size=2,            # Only 2 connections
        max_overflow=3,         # Max 5 total connections
    )
    """
    print(low_mem_config)
    print("   ✓ Reduces memory footprint")
    
    # Test with actual SQLite (pool settings ignored but accepted)
    try:
        from ghost_kg.storage.database import KnowledgeDB
        db = KnowledgeDB(
            db_path=":memory:",
            pool_size=10,
            max_overflow=20,
        )
        print("\n5. Testing with SQLite (pool settings stored but not applied):")
        print(f"   ✓ Pool size: {db.db_manager.pool_size}")
        print(f"   ✓ Max overflow: {db.db_manager.max_overflow}")
        print(f"   ✓ Actual pool: {db.db_manager.engine.pool.__class__.__name__}")
        print("   (SQLite uses StaticPool for :memory: or NullPool for files)")
        
        print("\n✅ Pool configuration demo complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():

    """Run all demonstrations."""
    print("\n" + "="*70)
    print("GhostKG Multi-Database Support Demonstration")
    print("="*70)
    print("\nGhostKG now supports:")
    print("  • SQLite (default) - file-based or in-memory")
    print("  • PostgreSQL - scalable, concurrent access")
    print("  • MySQL - widely deployed, cloud-friendly")
    
    # Run demos
    demo_sqlite()
    demo_postgresql()
    demo_mysql()
    demo_multi_database()
    demo_pool_configuration()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nConnection String Examples:")
    print("  SQLite:     'sqlite:///path/to/db.db'  or just 'path/to/db.db'")
    print("  PostgreSQL: 'postgresql://user:pass@host:port/dbname'")
    print("  MySQL:      'mysql+pymysql://user:pass@host:port/dbname'")
    print("\nUsage:")
    print("  agent = GhostAgent('name', db_path='connection_string')")
    print("\nNote: For PostgreSQL/MySQL, the database must exist.")
    print("      GhostKG creates tables but not databases.")
    print()


if __name__ == "__main__":
    main()
