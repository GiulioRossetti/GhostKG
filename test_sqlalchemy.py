#!/usr/bin/env python3
"""
Test script to verify SQLAlchemy implementation works correctly.
"""

import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg.storage.database_sqlalchemy import KnowledgeDB, NodeState
from ghost_kg import Rating
import datetime


def test_basic_operations():
    """Test basic database operations."""
    print("="*70)
    print("TEST: Basic SQLAlchemy Database Operations")
    print("="*70)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        # Test 1: Initialize database
        print("\n1. Initializing database...")
        db = KnowledgeDB(db_path=db_path)
        print("✓ Database initialized")
        
        # Test 2: Upsert node
        print("\n2. Inserting node...")
        db.upsert_node("Alice", "Python")
        print("✓ Node inserted")
        
        # Test 3: Get node
        print("\n3. Retrieving node...")
        node = db.get_node("Alice", "Python")
        assert node is not None
        assert node["owner_id"] == "Alice"
        assert node["id"] == "Python"
        print(f"✓ Node retrieved: {node['owner_id']}/{node['id']}")
        
        # Test 4: Upsert with FSRS state
        print("\n4. Updating node with FSRS state...")
        fsrs_state = NodeState(
            stability=5.0,
            difficulty=3.5,
            last_review=datetime.datetime.now(datetime.timezone.utc),
            reps=2,
            state=1
        )
        db.upsert_node("Alice", "Python", fsrs_state=fsrs_state)
        node = db.get_node("Alice", "Python")
        assert node["stability"] == 5.0
        assert node["difficulty"] == 3.5
        print(f"✓ FSRS state updated: stability={node['stability']}, difficulty={node['difficulty']}")
        
        # Test 5: Add relation
        print("\n5. Adding relation...")
        db.add_relation("Alice", "Python", "is", "awesome", sentiment=0.8)
        print("✓ Relation added")
        
        # Test 6: Get agent stance
        print("\n6. Retrieving agent stance...")
        stance = db.get_agent_stance("Alice", "Python")
        print(f"✓ Agent stance retrieved: {len(stance)} edges")
        
        # Test 7: Log interaction
        print("\n7. Logging interaction...")
        uuid_result = db.log_interaction(
            "Alice", 
            "test", 
            "test content", 
            {"key": "value"}
        )
        print(f"✓ Interaction logged: UUID={uuid_result}")
        
        # Test 8: Sentiment validation
        print("\n8. Testing sentiment validation...")
        try:
            db.add_relation("Alice", "Python", "is", "bad", sentiment=2.0)
            print("✗ Sentiment validation failed - should have raised error")
            return False
        except Exception as e:
            print(f"✓ Sentiment validation works: {e}")
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        
        # Cleanup
        db.close()
        os.unlink(db_path)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_postgresql():
    """Test PostgreSQL connection (if available)."""
    print("\n" + "="*70)
    print("TEST: PostgreSQL Connection")
    print("="*70)
    
    # Skip if PostgreSQL not available
    db_url = os.environ.get("POSTGRES_URL")
    if not db_url:
        print("⊘ Skipping - POSTGRES_URL not set")
        return True
    
    try:
        print(f"\n1. Connecting to PostgreSQL: {db_url[:30]}...")
        db = KnowledgeDB(db_url=db_url)
        print("✓ Connected to PostgreSQL")
        
        print("\n2. Testing operations...")
        db.upsert_node("TestUser", "TestNode")
        node = db.get_node("TestUser", "TestNode")
        assert node is not None
        print("✓ PostgreSQL operations work")
        
        db.close()
        print("\n✅ PostgreSQL test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ PostgreSQL test failed: {e}")
        return False


def test_mysql():
    """Test MySQL connection (if available)."""
    print("\n" + "="*70)
    print("TEST: MySQL Connection")
    print("="*70)
    
    # Skip if MySQL not available
    db_url = os.environ.get("MYSQL_URL")
    if not db_url:
        print("⊘ Skipping - MYSQL_URL not set")
        return True
    
    try:
        print(f"\n1. Connecting to MySQL: {db_url[:30]}...")
        db = KnowledgeDB(db_url=db_url)
        print("✓ Connected to MySQL")
        
        print("\n2. Testing operations...")
        db.upsert_node("TestUser", "TestNode")
        node = db.get_node("TestUser", "TestNode")
        assert node is not None
        print("✓ MySQL operations work")
        
        db.close()
        print("\n✅ MySQL test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ MySQL test failed: {e}")
        return False


if __name__ == "__main__":
    results = []
    
    # Run tests
    results.append(("Basic Operations", test_basic_operations()))
    results.append(("PostgreSQL", test_postgresql()))
    results.append(("MySQL", test_mysql()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Exit code
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)
