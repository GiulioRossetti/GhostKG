import sqlite3
import json
import datetime
from dataclasses import dataclass


@dataclass
class NodeState:
    stability: float
    difficulty: float
    last_review: datetime.datetime
    reps: int
    state: int


class KnowledgeDB:
    def __init__(self, db_path="agent_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
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

    # ... [upsert_node remains the same] ...
    def upsert_node(
        self, owner_id, node_id, fsrs_state: NodeState = None, timestamp=None
    ):
        ts = timestamp or datetime.datetime.now(datetime.timezone.utc)
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

    # UPDATED: Add sentiment argument
    def add_relation(
        self, owner_id, source, relation, target, sentiment=0.0, timestamp=None
    ):
        ts = timestamp or datetime.datetime.now(datetime.timezone.utc)

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

    # ... [log_interaction and getters remain the same] ...
    def log_interaction(self, agent, action, content, annotations, timestamp=None):
        ts = timestamp or datetime.datetime.now(datetime.timezone.utc)
        self.conn.execute(
            "INSERT INTO logs (agent_name, action_type, content, annotations, timestamp) VALUES (?, ?, ?, ?, ?)",
            (agent, action, content, json.dumps(annotations), ts),
        )
        self.conn.commit()

    def get_node(self, owner_id, node_id):
        return self.conn.execute(
            "SELECT * FROM nodes WHERE owner_id = ? AND id = ?", (owner_id, node_id)
        ).fetchone()

    def get_agent_stance(self, owner_id, topic, current_time=None):
        """
        Retrieves agent beliefs.
        """
        # Default to now if not provided, but simulation SHOULD provide it.
        ts = current_time or datetime.datetime.now(datetime.timezone.utc)

        search_term = f"%{topic}%"

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

    def get_world_knowledge(self, owner_id, topic, limit=10):
        search_term = f"%{topic}%"
        return self.conn.execute(
            """
                                 SELECT source, relation, target FROM edges
                                 WHERE owner_id = ? AND source != 'I' AND source != ?
            AND (source LIKE ? OR target LIKE ?)
                                 ORDER BY created_at DESC LIMIT ?
                                 """,
            (owner_id, owner_id, search_term, search_term, limit),
        ).fetchall()
