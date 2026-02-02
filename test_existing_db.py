#!/usr/bin/env python3
"""
Test script to verify GhostKG works with existing SQLite databases.

This script tests:
1. Creating a new database from scratch
2. Using an existing empty database
3. Using an existing database with other tables
4. Using an existing database that already has GhostKG tables
"""

import sqlite3
import os
import tempfile
from ghost_kg import GhostAgent, Rating


def test_new_database():
    """Test 1: Create a new database from scratch (file doesn't exist)."""
    print("\n" + "="*70)
    print("TEST 1: New Database (file doesn't exist)")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    # Delete the file so it doesn't exist
    os.unlink(db_path)
    
    assert not os.path.exists(db_path), "Database file should not exist yet"
    print(f"✓ Database file doesn't exist: {db_path}")
    
    # Create agent - should create the database
    agent = GhostAgent("Alice", db_path=db_path)
    
    assert os.path.exists(db_path), "Database file should now exist"
    print(f"✓ Database file created: {db_path}")
    
    # Test basic operations
    agent.learn_triplet("Python", "is", "awesome", Rating.Good)
    print("✓ Successfully learned a triplet")
    
    # Verify tables exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    expected_tables = {'nodes', 'edges', 'logs'}
    assert expected_tables.issubset(set(tables)), f"Expected tables {expected_tables}, got {tables}"
    print(f"✓ All expected tables created: {tables}")
    
    # Cleanup
    os.unlink(db_path)
    print("✓ Test 1 PASSED")


def test_existing_empty_database():
    """Test 2: Use an existing empty database."""
    print("\n" + "="*70)
    print("TEST 2: Existing Empty Database")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    # Create an empty database
    conn = sqlite3.connect(db_path)
    conn.close()
    
    assert os.path.exists(db_path), "Empty database should exist"
    print(f"✓ Empty database exists: {db_path}")
    
    # Use GhostKG with existing empty database
    agent = GhostAgent("Bob", db_path=db_path)
    print("✓ GhostAgent connected to existing empty database")
    
    # Test operations
    agent.learn_triplet("AI", "requires", "data", Rating.Easy)
    print("✓ Successfully learned a triplet")
    
    # Verify tables were created
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    expected_tables = {'nodes', 'edges', 'logs'}
    assert expected_tables.issubset(set(tables)), f"Expected tables {expected_tables}, got {tables}"
    print(f"✓ All expected tables created: {tables}")
    
    # Cleanup
    os.unlink(db_path)
    print("✓ Test 2 PASSED")


def test_existing_database_with_other_tables():
    """Test 3: Use an existing database that has other tables."""
    print("\n" + "="*70)
    print("TEST 3: Existing Database with Other Tables")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    # Create a database with some other tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL
        )
    """)
    
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", 
                   ("John Doe", "john@example.com"))
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", 
                   ("Widget", 19.99))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Created database with existing tables: users, products")
    
    # Use GhostKG with this database
    agent = GhostAgent("Charlie", db_path=db_path)
    print("✓ GhostAgent connected to existing database with other tables")
    
    # Test GhostKG operations
    agent.learn_triplet("Testing", "is", "important", Rating.Good)
    print("✓ Successfully learned a triplet")
    
    # Verify all tables exist (both original and GhostKG tables)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Verify original tables still exist
    assert 'users' in tables, "Original 'users' table should still exist"
    assert 'products' in tables, "Original 'products' table should still exist"
    print("✓ Original tables (users, products) still exist")
    
    # Verify GhostKG tables were created
    expected_tables = {'nodes', 'edges', 'logs'}
    assert expected_tables.issubset(set(tables)), f"Expected GhostKG tables {expected_tables}"
    print(f"✓ GhostKG tables created: {expected_tables}")
    
    # Verify original data is intact
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    assert user_count == 1, "Original user data should be intact"
    
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    assert product_count == 1, "Original product data should be intact"
    print("✓ Original data is intact")
    
    conn.close()
    
    # Cleanup
    os.unlink(db_path)
    print("✓ Test 3 PASSED")


def test_existing_database_with_ghostkg_tables():
    """Test 4: Use an existing database that already has GhostKG tables."""
    print("\n" + "="*70)
    print("TEST 4: Existing Database with GhostKG Tables")
    print("="*70)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    # First agent creates the tables and adds data
    agent1 = GhostAgent("Agent1", db_path=db_path)
    agent1.learn_triplet("Machine", "learning", "AI", Rating.Good)
    agent1.learn_triplet("Deep", "learning", "Neural Networks", Rating.Easy)
    print("✓ First agent created tables and added data")
    
    # Count initial data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM edges")
    initial_edge_count = cursor.fetchone()[0]
    conn.close()
    print(f"✓ Initial edge count: {initial_edge_count}")
    
    # Second agent connects to the same database
    agent2 = GhostAgent("Agent2", db_path=db_path)
    print("✓ Second agent connected to existing database with GhostKG tables")
    
    # Second agent adds more data
    agent2.learn_triplet("Python", "is", "popular", Rating.Good)
    print("✓ Second agent successfully added data")
    
    # Verify both agents' data exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM edges")
    final_edge_count = cursor.fetchone()[0]
    assert final_edge_count > initial_edge_count, "New data should be added"
    print(f"✓ Final edge count: {final_edge_count} (increased from {initial_edge_count})")
    
    cursor.execute("SELECT DISTINCT owner_id FROM nodes")
    owners = [row[0] for row in cursor.fetchall()]
    assert 'Agent1' in owners, "Agent1's data should exist"
    assert 'Agent2' in owners, "Agent2's data should exist"
    print(f"✓ Both agents' data exists: {owners}")
    
    conn.close()
    
    # Cleanup
    os.unlink(db_path)
    print("✓ Test 4 PASSED")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("TESTING: GhostKG with Existing SQLite Databases")
    print("="*70)
    
    try:
        test_new_database()
        test_existing_empty_database()
        test_existing_database_with_other_tables()
        test_existing_database_with_ghostkg_tables()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nConclusion: GhostKG successfully works with:")
        print("  ✓ New database files (creates from scratch)")
        print("  ✓ Existing empty databases")
        print("  ✓ Existing databases with other tables (preserves them)")
        print("  ✓ Existing databases with GhostKG tables (reuses them)")
        print("\nNo changes needed - functionality already works!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
