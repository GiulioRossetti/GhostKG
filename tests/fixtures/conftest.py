"""Shared pytest fixtures for GhostKG tests."""
import pytest
import datetime
import tempfile
from pathlib import Path
from ghost_kg import AgentManager, GhostAgent, KnowledgeDB


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary database path for tests."""
    db_path = tmp_path / "test_agent.db"
    return str(db_path)


@pytest.fixture
def temp_manager(tmp_path):
    """Provide a temporary AgentManager for tests."""
    db_path = tmp_path / "test_manager.db"
    return AgentManager(str(db_path))


@pytest.fixture
def temp_agent(temp_db_path):
    """Provide a temporary GhostAgent for tests."""
    agent = GhostAgent("TestAgent", db_path=temp_db_path)
    return agent


@pytest.fixture
def temp_db(tmp_path):
    """Provide a temporary KnowledgeDB for tests."""
    db_path = tmp_path / "test_knowledge.db"
    return KnowledgeDB(str(db_path))


@pytest.fixture
def current_time():
    """Provide current UTC time for tests."""
    return datetime.datetime.now(datetime.timezone.utc)


@pytest.fixture
def sample_triplets():
    """Provide sample triplets for testing."""
    return [
        ("Alice", "knows", "Bob"),
        ("Bob", "likes", "Python"),
        ("Python", "is", "programming_language"),
        ("climate_change", "is", "urgent"),
        ("AI", "transforms", "society"),
    ]


@pytest.fixture
def sample_triplets_with_sentiment():
    """Provide sample triplets with sentiment values."""
    return [
        ("happiness", "positive", 0.9),
        ("sadness", "negative", -0.8),
        ("neutral", "fact", 0.0),
        ("excitement", "positive", 0.7),
        ("anger", "negative", -0.6),
    ]


@pytest.fixture
def multi_agent_setup(tmp_path):
    """Provide a setup with multiple agents for testing."""
    db_path = tmp_path / "multi_agent.db"
    manager = AgentManager(str(db_path))
    
    # Create agents
    alice = manager.create_agent("Alice")
    bob = manager.create_agent("Bob")
    charlie = manager.create_agent("Charlie")
    
    # Set initial time
    now = datetime.datetime.now(datetime.timezone.utc)
    manager.set_agent_time("Alice", now)
    manager.set_agent_time("Bob", now)
    manager.set_agent_time("Charlie", now)
    
    return {
        "manager": manager,
        "agents": {"Alice": alice, "Bob": bob, "Charlie": charlie},
        "time": now,
    }


@pytest.fixture
def populated_agent(temp_manager, current_time):
    """Provide an agent with pre-populated knowledge."""
    agent_name = "PopulatedAgent"
    agent = temp_manager.create_agent(agent_name)
    temp_manager.set_agent_time(agent_name, current_time)
    
    # Add some knowledge
    triplets = [
        ("AI", "is", "powerful"),
        ("climate", "needs", "attention"),
        ("Python", "is", "popular"),
        ("data", "drives", "insights"),
    ]
    
    for source, relation, target in triplets:
        temp_manager.learn_triplet(agent_name, source, relation, target)
    
    return {
        "manager": temp_manager,
        "agent": agent,
        "agent_name": agent_name,
        "time": current_time,
    }


@pytest.fixture(autouse=True)
def cleanup_test_dbs():
    """Automatically cleanup test databases after each test."""
    # Setup: nothing needed
    yield
    # Teardown: cleanup happens automatically with tmp_path
    pass
