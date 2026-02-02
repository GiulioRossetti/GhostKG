"""Unit tests for using GhostKG with existing SQLite databases."""
import pytest
import sqlite3
import tempfile
import os
from ghost_kg import GhostAgent, KnowledgeDB, Rating


class TestExistingDatabases:
    """Test GhostKG integration with existing SQLite databases."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except:
            pass
    
    def test_new_database_creation(self, temp_db_path):
        """Test that GhostKG creates a new database when file doesn't exist."""
        # Delete the file so it doesn't exist
        os.unlink(temp_db_path)
        assert not os.path.exists(temp_db_path)
        
        # Create KnowledgeDB - should create the file
        db = KnowledgeDB(temp_db_path)
        assert os.path.exists(temp_db_path)
        
        # Verify tables exist
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        assert 'kg_nodes' in tables
        assert 'kg_edges' in tables
        assert 'kg_logs' in tables
    
    def test_existing_empty_database(self, temp_db_path):
        """Test that GhostKG works with an existing empty database."""
        # Create an empty database
        conn = sqlite3.connect(temp_db_path)
        conn.close()
        assert os.path.exists(temp_db_path)
        
        # Connect with GhostKG
        db = KnowledgeDB(temp_db_path)
        
        # Verify tables were created
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        assert 'kg_nodes' in tables
        assert 'kg_edges' in tables
        assert 'kg_logs' in tables
    
    def test_existing_database_with_other_tables(self, temp_db_path):
        """Test that GhostKG preserves existing tables in the database."""
        # Create database with other tables
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        cursor.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        conn.commit()
        conn.close()
        
        # Connect with GhostKG
        db = KnowledgeDB(temp_db_path)
        
        # Verify both original and GhostKG tables exist
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        assert 'users' in tables  # Original table preserved
        assert 'kg_nodes' in tables  # GhostKG table added
        assert 'kg_edges' in tables  # GhostKG table added
        assert 'kg_logs' in tables   # GhostKG table added
        
        # Verify original data is intact
        cursor.execute("SELECT COUNT(*) FROM users")
        assert cursor.fetchone()[0] == 1
    
    def test_existing_database_with_ghostkg_tables(self, temp_db_path):
        """Test that GhostKG reuses existing GhostKG tables."""
        # First agent creates tables and adds data
        agent1 = GhostAgent("Agent1", db_path=temp_db_path)
        agent1.learn_triplet("Python", "is", "great", Rating.Good)
        
        # Get initial count
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM kg_edges")
        initial_count = cursor.fetchone()[0]
        conn.close()
        
        # Second agent connects to same database
        agent2 = GhostAgent("Agent2", db_path=temp_db_path)
        agent2.learn_triplet("AI", "uses", "Python", Rating.Easy)
        
        # Verify both agents' data exists
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM kg_edges")
        final_count = cursor.fetchone()[0]
        conn.close()
        
        assert final_count == initial_count + 1
    
    def test_agent_with_existing_database(self, temp_db_path):
        """Test GhostAgent creation with existing database containing other tables."""
        # Create database with application-specific table
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE app_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("INSERT INTO app_config (key, value) VALUES (?, ?)", 
                      ("version", "1.0.0"))
        conn.commit()
        conn.close()
        
        # Create agent with this database
        agent = GhostAgent("TestAgent", db_path=temp_db_path)
        agent.learn_triplet("Testing", "is", "important", Rating.Good)
        
        # Verify app table still exists with data
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = ?", ("version",))
        result = cursor.fetchone()
        assert result[0] == "1.0.0"
        conn.close()
