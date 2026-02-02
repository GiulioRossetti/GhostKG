import datetime
import json
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Tuple

from ..utils.exceptions import DatabaseError, ValidationError
from ..utils.time_utils import SimulationTime, parse_time_input


@dataclass
class NodeState:
    """
    Represents the FSRS memory state of a knowledge node.

    Attributes:
        stability (float): Memory stability value
        difficulty (float): Memory difficulty value
        last_review (datetime.datetime): Timestamp of last review
        reps (int): Number of repetitions
        state (int): Current state (0=New, 1=Learning, 2=Review)
    """

    stability: float
    difficulty: float
    last_review: Optional[datetime.datetime]
    reps: int
    state: int


class KnowledgeDB:
    def __init__(self, db_path: str = "agent_memory.db", store_log_content: bool = False) -> None:
        """
        Initialize database connection and schema.

        Args:
            db_path (str): Path to SQLite database file
            store_log_content (bool): If True, stores full content in log table.
                                     If False (default), stores UUID instead of content.

        Returns:
            None

        Raises:
            DatabaseError: If connection or schema initialization fails
        """
        self.store_log_content = store_log_content
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._init_schema()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database at {db_path}: {e}") from e

    def _init_schema(self) -> None:
        """
        Initialize database schema.

        Returns:
            None

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
                                                            sim_day INTEGER, sim_hour INTEGER,
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
                                                            sim_day INTEGER, sim_hour INTEGER,
                                                            PRIMARY KEY (owner_id, source, target, relation),
                           FOREIGN KEY(owner_id, source) REFERENCES nodes(owner_id, id),
                           FOREIGN KEY(owner_id, target) REFERENCES nodes(owner_id, id)
                           )
                       """)

            cursor.execute("""
                       CREATE TABLE IF NOT EXISTS logs (
                                                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                           agent_name TEXT, action_type TEXT, content TEXT,
                                                           content_uuid TEXT, annotations JSON,
                                                           timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                           sim_day INTEGER, sim_hour INTEGER
                       )
                       """)

            # Performance indexes for common queries
            # Index for querying edges by owner and source (e.g., get_relations)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_owner_source 
                ON edges(owner_id, source)
            """)

            # Index for querying edges by owner and target (e.g., reverse lookups)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_owner_target 
                ON edges(owner_id, target)
            """)

            # Index for temporal queries on edges (most recent first)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_created 
                ON edges(owner_id, created_at DESC)
            """)

            # Index for nodes by last review time (memory recency queries)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nodes_last_review 
                ON nodes(owner_id, last_review DESC)
            """)

            # Index for nodes by owner (common filter)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nodes_owner 
                ON nodes(owner_id)
            """)

            # Index for logs by agent and timestamp (query agent history)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_agent_time 
                ON logs(agent_name, timestamp DESC)
            """)

            # Index for logs by action type (filter by action)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_action 
                ON logs(action_type, timestamp DESC)
            """)

            # Migrate existing tables to add round-based time columns if needed
            self._migrate_schema(cursor)

            self.conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize schema: {e}") from e

    def _migrate_schema(self, cursor: sqlite3.Cursor) -> None:
        """
        Migrate existing database schema to add round-based time columns.
        
        Args:
            cursor: Database cursor
            
        Returns:
            None
        """
        # Check if nodes table needs migration
        cursor.execute("PRAGMA table_info(nodes)")
        nodes_columns = {row[1] for row in cursor.fetchall()}
        
        if "sim_day" not in nodes_columns:
            cursor.execute("ALTER TABLE nodes ADD COLUMN sim_day INTEGER")
        if "sim_hour" not in nodes_columns:
            cursor.execute("ALTER TABLE nodes ADD COLUMN sim_hour INTEGER")
        
        # Check if edges table needs migration
        cursor.execute("PRAGMA table_info(edges)")
        edges_columns = {row[1] for row in cursor.fetchall()}
        
        if "sim_day" not in edges_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN sim_day INTEGER")
        if "sim_hour" not in edges_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN sim_hour INTEGER")
        
        # Check if logs table needs migration
        cursor.execute("PRAGMA table_info(logs)")
        logs_columns = {row[1] for row in cursor.fetchall()}
        
        if "sim_day" not in logs_columns:
            cursor.execute("ALTER TABLE logs ADD COLUMN sim_day INTEGER")
        if "sim_hour" not in logs_columns:
            cursor.execute("ALTER TABLE logs ADD COLUMN sim_hour INTEGER")

    def upsert_node(
        self,
        owner_id: str,
        node_id: str,
        fsrs_state: Optional[NodeState] = None,
        timestamp: Optional[Union[datetime.datetime, SimulationTime]] = None,
    ) -> None:
        """
        Upsert a node with optional FSRS state.

        Args:
            owner_id (str): Owner/agent identifier
            node_id (str): Node identifier
            fsrs_state (Optional[NodeState]): Optional FSRS state to store
            timestamp (Optional[Union[datetime.datetime, SimulationTime]]): 
                Optional timestamp (defaults to now). Can be a datetime or SimulationTime object.

        Returns:
            None

        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If database operation fails
        """
        if not owner_id or not node_id:
            raise ValidationError("owner_id and node_id are required")

        # Handle timestamp
        if timestamp is None:
            ts = datetime.datetime.now(datetime.timezone.utc)
            sim_day = None
            sim_hour = None
        elif isinstance(timestamp, SimulationTime):
            ts = timestamp.to_datetime()
            round_time = timestamp.to_round()
            sim_day = round_time[0] if round_time else None
            sim_hour = round_time[1] if round_time else None
        else:
            # datetime.datetime
            ts = timestamp
            sim_day = None
            sim_hour = None

        try:
            if fsrs_state:
                self.conn.execute(
                    """
                                  INSERT INTO nodes (owner_id, id, stability, difficulty, last_review, reps, state, created_at, sim_day, sim_hour)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                      ON CONFLICT(owner_id, id) DO UPDATE SET
                                      stability=excluded.stability, difficulty=excluded.difficulty,
                                                                       last_review=excluded.last_review, reps=excluded.reps, state=excluded.state,
                                                                       sim_day=excluded.sim_day, sim_hour=excluded.sim_hour
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
                        sim_day,
                        sim_hour,
                    ),
                )
            else:
                self.conn.execute(
                    "INSERT OR IGNORE INTO nodes (owner_id, id, created_at, sim_day, sim_hour) VALUES (?, ?, ?, ?, ?)",
                    (owner_id, node_id, ts, sim_day, sim_hour),
                )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to upsert node {node_id} for {owner_id}: {e}") from e

    def add_relation(
        self,
        owner_id: str,
        source: str,
        relation: str,
        target: str,
        sentiment: float = 0.0,
        timestamp: Optional[Union[datetime.datetime, SimulationTime]] = None,
    ) -> None:
        """
        Add a relation between nodes.

        Args:
            owner_id (str): Owner/agent identifier
            source (str): Source node identifier
            relation (str): Relation type
            target (str): Target node identifier
            sentiment (float): Sentiment value (-1.0 to 1.0)
            timestamp (Optional[Union[datetime.datetime, SimulationTime]]): 
                Optional timestamp (defaults to now). Can be a datetime or SimulationTime object.

        Returns:
            None

        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If database operation fails
        """
        if not owner_id or not source or not relation or not target:
            raise ValidationError("owner_id, source, relation, and target are required")

        # Handle None sentiment by using default value
        if sentiment is None:
            sentiment = 0.0

        if not -1.0 <= sentiment <= 1.0:
            raise ValidationError(f"sentiment must be between -1.0 and 1.0, got {sentiment}")

        # Handle timestamp
        if timestamp is None:
            ts = datetime.datetime.now(datetime.timezone.utc)
            sim_day = None
            sim_hour = None
        elif isinstance(timestamp, SimulationTime):
            ts = timestamp.to_datetime()
            round_time = timestamp.to_round()
            sim_day = round_time[0] if round_time else None
            sim_hour = round_time[1] if round_time else None
        else:
            # datetime.datetime
            ts = timestamp
            sim_day = None
            sim_hour = None

        try:
            self.upsert_node(owner_id, source, timestamp=timestamp)
            self.upsert_node(owner_id, target, timestamp=timestamp)

            self.conn.execute(
                """
                INSERT OR REPLACE INTO edges (owner_id, source, target, relation, sentiment, created_at, sim_day, sim_hour)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (owner_id, source, target, relation, sentiment, ts, sim_day, sim_hour),
            )
            self.conn.commit()
        except ValidationError:
            raise  # Re-raise validation errors
        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseError(
                f"Failed to add relation {source} -{relation}-> {target} for {owner_id}: {e}"
            ) from e

    def log_interaction(
        self,
        agent: str,
        action: str,
        content: str,
        annotations: Dict[str, Any],
        timestamp: Optional[Union[datetime.datetime, SimulationTime]] = None,
        store_content: Optional[bool] = None,
        content_uuid: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log an agent interaction.

        Args:
            agent (str): Agent name
            action (str): Action type
            content (str): Content of the interaction
            annotations (Dict[str, Any]): Additional metadata (will be JSON-encoded)
            timestamp (Optional[Union[datetime.datetime, SimulationTime]]): 
                Optional timestamp (defaults to now). Can be a datetime or SimulationTime object.
            store_content (Optional[bool]): If True, stores content in the log table.
                                           If False, generates and stores a UUID instead.
                                           If None (default), uses database instance setting.
            content_uuid (Optional[str]): Optional UUID to use when content is not stored.
                                         If not provided, a UUID will be auto-generated.
                                         Only valid when store_content is False.

        Returns:
            Optional[str]: The content UUID if store_content is False, None otherwise

        Raises:
            ValidationError: If parameters are invalid
            DatabaseError: If database operation fails
        """
        if not agent or not action:
            raise ValidationError("agent and action are required")

        # Handle timestamp
        if timestamp is None:
            ts = datetime.datetime.now(datetime.timezone.utc)
            sim_day = None
            sim_hour = None
        elif isinstance(timestamp, SimulationTime):
            ts = timestamp.to_datetime()
            round_time = timestamp.to_round()
            sim_day = round_time[0] if round_time else None
            sim_hour = round_time[1] if round_time else None
        else:
            # datetime.datetime
            ts = timestamp
            sim_day = None
            sim_hour = None

        # Use instance default if not specified
        should_store = store_content if store_content is not None else self.store_log_content

        # Validate content_uuid parameter usage
        if content_uuid is not None:
            if should_store:
                raise ValidationError(
                    "content_uuid can only be specified when store_content is False"
                )
            # Validate UUID format
            try:
                uuid.UUID(content_uuid)
            except (ValueError, AttributeError) as e:
                raise ValidationError(f"Invalid UUID format: {content_uuid}") from e

        # Use provided UUID or generate one if not storing content
        uuid_to_use = None
        stored_content = content if should_store else None

        if not should_store:
            uuid_to_use = content_uuid if content_uuid is not None else str(uuid.uuid4())

        try:
            query = """
                INSERT INTO logs (agent_name, action_type, content, content_uuid,
                                 annotations, timestamp, sim_day, sim_hour)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(
                query,
                (agent, action, stored_content, uuid_to_use, json.dumps(annotations), ts, sim_day, sim_hour),
            )
            self.conn.commit()
            return uuid_to_use
        except (sqlite3.Error, TypeError) as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to log interaction for {agent}: {e}") from e

    def get_node(self, owner_id: str, node_id: str) -> Optional[sqlite3.Row]:
        """
        Get a node by ID.

        Args:
            owner_id (str): Owner/agent identifier
            node_id (str): Node identifier

        Returns:
            Optional[sqlite3.Row]: sqlite3.Row or None if not found

        Raises:
            DatabaseError: If query fails
        """
        try:
            result = self.conn.execute(
                "SELECT * FROM nodes WHERE owner_id = ? AND id = ?", (owner_id, node_id)
            ).fetchone()
            return result  # type: ignore[no-any-return]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get node {node_id} for {owner_id}: {e}") from e

    def get_agent_stance(
        self, owner_id: str, topic: str, current_time: Optional[Union[datetime.datetime, SimulationTime]] = None
    ) -> List[sqlite3.Row]:
        """
        Retrieves agent beliefs.

        Args:
            owner_id (str): Owner/agent identifier
            topic (str): Topic to search for
            current_time (Optional[Union[datetime.datetime, SimulationTime]]): Optional current simulation time

        Returns:
            List[sqlite3.Row]: List of sqlite3.Row objects

        Raises:
            DatabaseError: If query fails
        """
        # Default to now if not provided, but simulation SHOULD provide it.
        if current_time is None:
            ts = datetime.datetime.now(datetime.timezone.utc)
        elif isinstance(current_time, SimulationTime):
            ts = current_time.to_datetime()
            if ts is None:
                # Round-based mode without datetime - use current time as fallback
                ts = datetime.datetime.now(datetime.timezone.utc)
        else:
            ts = current_time

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
            return self.conn.execute(query, (owner_id, owner_id, search_term, ts)).fetchall()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get agent stance for {owner_id} on {topic}: {e}") from e

    def get_world_knowledge(self, owner_id: str, topic: str, limit: int = 10) -> List[sqlite3.Row]:
        """
        Get world knowledge (facts from others) about a topic with sentiment.

        Args:
            owner_id (str): Owner/agent identifier
            topic (str): Topic to search for
            limit (int): Maximum number of results

        Returns:
            List[sqlite3.Row]: List of sqlite3.Row objects with source, relation, target, sentiment

        Raises:
            DatabaseError: If query fails
        """
        search_term = f"%{topic}%"

        try:
            return self.conn.execute(
                """
                                     SELECT source, relation, target, sentiment FROM edges
                                     WHERE owner_id = ? AND source != 'I' AND source != ?
                AND (source LIKE ? OR target LIKE ?)
                                     ORDER BY created_at DESC LIMIT ?
                                     """,
                (owner_id, owner_id, search_term, search_term, limit),
            ).fetchall()
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to get world knowledge for {owner_id} on {topic}: {e}"
            ) from e
