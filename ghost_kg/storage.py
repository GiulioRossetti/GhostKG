import sqlite3
import json
import datetime
from dataclasses import dataclass
from typing import Optional, List
from .exceptions import DatabaseError, ValidationError


@dataclass
class NodeState:
    stability: float
    difficulty: float
    last_review: datetime.datetime
    reps: int
    state: int


class KnowledgeDB:
    def __init__(self, db_path="agent_memory.db"):
        """Initialize database connection and schema.
        
        Args:
            db_path: Path to SQLite database file
            
        Raises:
            DatabaseError: If connection or schema initialization fails
        """
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._init_schema()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database at {db_path}: {e}") from e

    def _init_schema(self):
        """Initialize database schema.
        
        Raises:
            DatabaseError: If schema creation fails
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                       CREATE TABLE IF NOT EXISTS nodes (
                                                            owner_id TEXT, id TEXT,
                                                            stability REAL DEFAULT 0, difficulty REAL DEFAULT 0,
                                                            last_review TIMESTAMP, reps INTEGER DEFAULT 0, state INTEGER DEFAULT 0,
                                                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                            PRIMARY KEY (owner_id, id)
                           )
                       """)

            # ADDED: sentiment column (REAL)
            cursor.execute("""
                       CREATE TABLE IF NOT EXISTS edges (
                                                            owner_id TEXT, source TEXT, target TEXT, relation TEXT,
                                                            weight REAL DEFAULT 1.0,
                                                            sentiment REAL DEFAULT 0.0, -- -1.0 (Hate) to 1.0 (Love)
                                                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                            PRIMARY KEY (owner_id, source, target, relation),
                           FOREIGN KEY(owner_id, source) REFERENCES nodes(owner_id, id),
                           FOREIGN KEY(owner_id, target) REFERENCES nodes(owner_id, id)
                           )
                       """)

            cursor.execute("""
                       CREATE TABLE IF NOT EXISTS logs (
                                                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                           agent_name TEXT, action_type TEXT, content TEXT, annotations JSON,
                                                           timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       """)
            self.conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize schema: {e}") from e

    # ... [upsert_node remains the same] ...
    def upsert_node(
        self, owner_id, node_id, fsrs_state: NodeState = None, timestamp=None
    ):
        """Upsert a node with optional FSRS state.
        
        Args:
            owner_id: Owner/agent identifier
            node_id: Node identifier
            fsrs_state: Optional FSRS state to store
            timestamp: Optional timestamp (defaults to now)
            
        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If database operation fails
        """
        if not owner_id or not node_id:
            raise ValidationError("owner_id and node_id are required")
            
        ts = timestamp or datetime.datetime.now(datetime.timezone.utc)
        
        try:
            if fsrs_state:
                self.conn.execute(
                    """
                                  INSERT INTO nodes (owner_id, id, stability, difficulty, last_review, reps, state, created_at)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                      ON CONFLICT(owner_id, id) DO UPDATE SET
                                      stability=excluded.stability, difficulty=excluded.difficulty,
                                                                       last_review=excluded.last_review, reps=excluded.reps, state=excluded.state
                                  """,
                    (
                        owner_id,
                        node_id,
                        fsrs_state.stability,
                        fsrs_state.difficulty,
                        fsrs_state.last_review,
                        fsrs_state.reps,
                        fsrs_state.state,
                        ts,
                    ),
                )
            else:
                self.conn.execute(
                    "INSERT OR IGNORE INTO nodes (owner_id, id, created_at) VALUES (?, ?, ?)",
                    (owner_id, node_id, ts),
                )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to upsert node {node_id} for {owner_id}: {e}") from e

    # UPDATED: Add sentiment argument
    def add_relation(
        self, owner_id, source, relation, target, sentiment=0.0, timestamp=None
    ):
        """Add a relation between nodes.
        
        Args:
            owner_id: Owner/agent identifier
            source: Source node identifier
            relation: Relation type
            target: Target node identifier
            sentiment: Sentiment value (-1.0 to 1.0)
            timestamp: Optional timestamp (defaults to now)
            
        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If database operation fails
        """
        if not owner_id or not source or not relation or not target:
            raise ValidationError("owner_id, source, relation, and target are required")
            
        if not -1.0 <= sentiment <= 1.0:
            raise ValidationError(f"sentiment must be between -1.0 and 1.0, got {sentiment}")
            
        ts = timestamp or datetime.datetime.now(datetime.timezone.utc)

        try:
            self.upsert_node(owner_id, source, timestamp=ts)
            self.upsert_node(owner_id, target, timestamp=ts)

            self.conn.execute(
                """
                INSERT OR REPLACE INTO edges (owner_id, source, target, relation, sentiment, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (owner_id, source, target, relation, sentiment, ts),
            )
            self.conn.commit()
        except ValidationError:
            raise  # Re-raise validation errors
        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(
                f"Failed to add relation {source} -{relation}-> {target} for {owner_id}: {e}"
            ) from e

    # ... [log_interaction and getters remain the same] ...
    def log_interaction(self, agent, action, content, annotations, timestamp=None):
        """Log an agent interaction.
        
        Args:
            agent: Agent name
            action: Action type
            content: Content of the interaction
            annotations: Additional metadata (will be JSON-encoded)
            timestamp: Optional timestamp (defaults to now)
            
        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If database operation fails
        """
        if not agent or not action:
            raise ValidationError("agent and action are required")
            
        ts = timestamp or datetime.datetime.now(datetime.timezone.utc)
        
        try:
            self.conn.execute(
                "INSERT INTO logs (agent_name, action_type, content, annotations, timestamp) VALUES (?, ?, ?, ?, ?)",
                (agent, action, content, json.dumps(annotations), ts),
            )
            self.conn.commit()
        except (sqlite3.Error, TypeError) as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to log interaction for {agent}: {e}") from e

    def get_node(self, owner_id, node_id):
        """Get a node by ID.
        
        Args:
            owner_id: Owner/agent identifier
            node_id: Node identifier
            
        Returns:
            sqlite3.Row or None if not found
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            return self.conn.execute(
                "SELECT * FROM nodes WHERE owner_id = ? AND id = ?", (owner_id, node_id)
            ).fetchone()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get node {node_id} for {owner_id}: {e}") from e

    def get_agent_stance(self, owner_id, topic, current_time=None):
        """
        Retrieves agent beliefs.
        
        Args:
            owner_id: Owner/agent identifier
            topic: Topic to search for
            current_time: Optional current simulation time
            
        Returns:
            List of sqlite3.Row objects
            
        Raises:
            DatabaseError: If query fails
        """
        # Default to now if not provided, but simulation SHOULD provide it.
        ts = current_time or datetime.datetime.now(datetime.timezone.utc)

        search_term = f"%{topic}%"

        try:
            # SQL logic:
            # 1. Source must be 'I' (or agent name)
            # 2. Target matches topic OR it was created in the last 60 mins OF SIMULATION TIME
            query = """
                    SELECT source, relation, target, sentiment FROM edges
                    WHERE owner_id = ?
                      AND (source = 'I' OR source = ?)
                      AND (
                        target LIKE ?
                            OR created_at >= datetime(?, '-60 minutes')
                        )
                    ORDER BY created_at DESC
                        LIMIT 8 \
                    """
            return self.conn.execute(
                query, (owner_id, owner_id, search_term, ts)
            ).fetchall()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get agent stance for {owner_id} on {topic}: {e}") from e

    def get_world_knowledge(self, owner_id, topic, limit=10):
        """Get world knowledge (facts from others) about a topic.
        
        Args:
            owner_id: Owner/agent identifier
            topic: Topic to search for
            limit: Maximum number of results
            
        Returns:
            List of sqlite3.Row objects
            
        Raises:
            DatabaseError: If query fails
        """
        search_term = f"%{topic}%"
        
        try:
            return self.conn.execute(
                """
                                     SELECT source, relation, target FROM edges
                                     WHERE owner_id = ? AND source != 'I' AND source != ?
                AND (source LIKE ? OR target LIKE ?)
                                     ORDER BY created_at DESC LIMIT ?
                                     """,
                (owner_id, owner_id, search_term, search_term, limit),
            ).fetchall()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get world knowledge for {owner_id} on {topic}: {e}") from e
