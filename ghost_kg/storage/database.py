"""
Database storage layer for GhostKG using SQLAlchemy ORM.

Supports SQLite (default), PostgreSQL, and MySQL.
"""

import datetime
import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import select, and_, or_, func
from sqlalchemy.dialects import postgresql, mysql, sqlite
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .engine import DatabaseManager
from .models import Node, Edge, Log
from ..utils.exceptions import DatabaseError, ValidationError
from ..utils.time_utils import SimulationTime


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
    """
    Knowledge graph database with multi-database support.
    
    Supports SQLite (default), PostgreSQL, and MySQL through SQLAlchemy ORM.
    """
    
    def __init__(
        self, 
        db_path: str = "agent_memory.db",
        db_url: Optional[str] = None,
        store_log_content: bool = False,
        echo: bool = False,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: Optional[float] = None,
        pool_recycle: Optional[int] = None,
    ) -> None:
        """
        Initialize database connection and schema.

        Args:
            db_path (str): Path to SQLite database file (legacy parameter)
            db_url (str): SQLAlchemy database URL (takes precedence over db_path)
                         Examples:
                         - SQLite: "sqlite:///path/to/db.db"
                         - PostgreSQL: "postgresql://user:pass@host:port/dbname"
                         - MySQL: "mysql+pymysql://user:pass@host:port/dbname"
            store_log_content (bool): If True, stores full content in log table.
                                     If False (default), stores UUID instead of content.
            echo (bool): Enable SQL query logging for debugging
            pool_size (int): Connection pool size (PostgreSQL/MySQL only, default: 5)
            max_overflow (int): Max overflow connections (PostgreSQL/MySQL only, default: 10)
            pool_timeout (float): Pool checkout timeout in seconds (PostgreSQL/MySQL only, default: 30)
            pool_recycle (int): Recycle connections after N seconds (MySQL default: 3600)

        Returns:
            None

        Raises:
            DatabaseError: If connection or schema initialization fails
        """
        self.store_log_content = store_log_content
        
        try:
            # Initialize database manager
            self.db_manager = DatabaseManager(
                db_url=db_url,
                db_path=db_path,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
            )
            
            # Create tables if they don't exist
            self.db_manager.create_tables()
            
            # Get a session for operations
            self._session: Optional[Session] = None
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {e}") from e
    
    @property
    def session(self) -> Session:
        """Get or create a database session."""
        if self._session is None or not self._session.is_active:
            self._session = self.db_manager.get_session()
        return self._session
    
    @property
    def conn(self):
        """
        Compatibility property for tests that access db.conn directly.
        
        Returns a mock object that provides cursor() method for raw SQL access.
        """
        class ConnectionMock:
            def __init__(self, db_instance):
                self.db = db_instance
            
            def cursor(self):
                """Return a cursor mock for raw SQL execution."""
                return CursorMock(self.db)
            
            def commit(self):
                """Commit the current session."""
                if self.db._session:
                    self.db._session.commit()
            
            def rollback(self):
                """Rollback the current session."""
                if self.db._session:
                    self.db._session.rollback()
        
        class CursorMock:
            def __init__(self, db_instance):
                self.db = db_instance
                self.session = db_instance.session
                self._result = None
            
            def execute(self, sql, params=None):
                """Execute raw SQL using SQLAlchemy."""
                from sqlalchemy import text
                
                # Convert positional parameters to dictionary for SQLAlchemy
                if params:
                    if isinstance(params, (list, tuple)):
                        # Convert SQL with ? placeholders to :p0, :p1, etc.
                        sql_converted = sql
                        param_dict = {}
                        for i, param in enumerate(params):
                            sql_converted = sql_converted.replace('?', f':p{i}', 1)
                            param_dict[f'p{i}'] = param
                        self._result = self.session.execute(text(sql_converted), param_dict)
                    else:
                        self._result = self.session.execute(text(sql), params)
                else:
                    self._result = self.session.execute(text(sql))
                
                self.session.commit()  # Auto-commit for compatibility
                return self._result
            
            def fetchall(self):
                """Fetch all results from the last query."""
                if self._result:
                    return self._result.fetchall()
                return []
            
            def fetchone(self):
                """Fetch one result from the last query."""
                if self._result:
                    return self._result.fetchone()
                return None
            
            def close(self):
                """Close cursor - no-op for SQLAlchemy."""
                if self._result:
                    self._result.close()
                    self._result = None
        
        return ConnectionMock(self)
    
    def _get_new_session(self) -> Session:
        """Create a new session for isolated operations."""
        return self.db_manager.get_session()
    
    def _execute_with_session(self, operation, *args, **kwargs):
        """Execute an operation with proper session management."""
        session = None
        try:
            session = self._get_new_session()
            result = operation(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()
    
    def close(self):
        """Close the database session."""
        if self._session:
            self._session.close()
            self._session = None
    
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
            def _upsert(session):
                # Check if node exists
                existing_node = session.query(Node).filter_by(
                    owner_id=owner_id,
                    id=node_id
                ).first()
                
                if existing_node:
                    # Update existing node
                    if fsrs_state:
                        existing_node.stability = fsrs_state.stability
                        existing_node.difficulty = fsrs_state.difficulty
                        existing_node.last_review = fsrs_state.last_review
                        existing_node.reps = fsrs_state.reps
                        existing_node.state = fsrs_state.state
                        existing_node.sim_day = sim_day
                        existing_node.sim_hour = sim_hour
                else:
                    # Create new node
                    node_data = {
                        "owner_id": owner_id,
                        "id": node_id,
                        "created_at": ts,
                        "sim_day": sim_day,
                        "sim_hour": sim_hour,
                    }
                    
                    if fsrs_state:
                        node_data.update({
                            "stability": fsrs_state.stability,
                            "difficulty": fsrs_state.difficulty,
                            "last_review": fsrs_state.last_review,
                            "reps": fsrs_state.reps,
                            "state": fsrs_state.state,
                        })
                    
                    new_node = Node(**node_data)
                    session.add(new_node)
            
            self._execute_with_session(_upsert)
            
        except SQLAlchemyError as e:
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
            session = self._get_new_session()
            
            # Ensure source and target nodes exist
            self.upsert_node(owner_id, source, timestamp=timestamp)
            self.upsert_node(owner_id, target, timestamp=timestamp)
            
            # Check if edge exists
            existing_edge = session.query(Edge).filter_by(
                owner_id=owner_id,
                source=source,
                target=target,
                relation=relation
            ).first()
            
            if existing_edge:
                # Update existing edge
                existing_edge.sentiment = sentiment
                existing_edge.created_at = ts
                existing_edge.sim_day = sim_day
                existing_edge.sim_hour = sim_hour
            else:
                # Create new edge
                new_edge = Edge(
                    owner_id=owner_id,
                    source=source,
                    target=target,
                    relation=relation,
                    sentiment=sentiment,
                    created_at=ts,
                    sim_day=sim_day,
                    sim_hour=sim_hour
                )
                session.add(new_edge)
            
            session.commit()
            session.close()
            
        except ValidationError:
            raise  # Re-raise validation errors
        except SQLAlchemyError as e:
            if session:
                session.rollback()
                session.close()
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
            session = self._get_new_session()
            
            new_log = Log(
                agent_name=agent,
                action_type=action,
                content=stored_content,
                content_uuid=uuid_to_use,
                annotations=json.dumps(annotations),
                timestamp=ts,
                sim_day=sim_day,
                sim_hour=sim_hour
            )
            
            session.add(new_log)
            session.commit()
            session.close()
            
            return uuid_to_use
            
        except (SQLAlchemyError, TypeError) as e:
            if session:
                session.rollback()
                session.close()
            raise DatabaseError(f"Failed to log interaction for {agent}: {e}") from e

    def get_node(self, owner_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.

        Args:
            owner_id (str): Owner/agent identifier
            node_id (str): Node identifier

        Returns:
            Optional[Dict[str, Any]]: Node data as dictionary or None if not found

        Raises:
            DatabaseError: If query fails
        """
        try:
            session = self._get_new_session()
            
            node = session.query(Node).filter_by(
                owner_id=owner_id,
                id=node_id
            ).first()
            
            session.close()
            
            if node:
                # Convert to dictionary for backward compatibility
                return {
                    "owner_id": node.owner_id,
                    "id": node.id,
                    "stability": node.stability,
                    "difficulty": node.difficulty,
                    "last_review": node.last_review,
                    "reps": node.reps,
                    "state": node.state,
                    "created_at": node.created_at,
                    "sim_day": node.sim_day,
                    "sim_hour": node.sim_hour,
                }
            return None
            
        except SQLAlchemyError as e:
            if session:
                session.close()
            raise DatabaseError(f"Failed to get node {node_id} for {owner_id}: {e}") from e

    def get_agent_stance(
        self, owner_id: str, topic: str, current_time: Optional[Union[datetime.datetime, SimulationTime]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves agent beliefs.

        Args:
            owner_id (str): Owner/agent identifier
            topic (str): Topic to search for
            current_time (Optional[Union[datetime.datetime, SimulationTime]]): Optional current simulation time

        Returns:
            List[Dict[str, Any]]: List of edge dictionaries

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
            session = self._get_new_session()
            
            # SQL logic:
            # 1. Source must be 'I' (or agent name)
            # 2. Target matches topic OR it was created in the last 60 mins OF SIMULATION TIME
            time_threshold = ts - datetime.timedelta(minutes=60)
            
            edges = session.query(Edge).filter(
                and_(
                    Edge.owner_id == owner_id,
                    or_(Edge.source == 'I', Edge.source == owner_id),
                    or_(
                        Edge.target.like(search_term),
                        Edge.created_at >= time_threshold
                    )
                )
            ).order_by(Edge.created_at.desc()).limit(8).all()
            
            session.close()
            
            # Convert to dictionaries
            return [
                {
                    "source": edge.source,
                    "relation": edge.relation,
                    "target": edge.target,
                    "sentiment": edge.sentiment,
                }
                for edge in edges
            ]
            
        except SQLAlchemyError as e:
            if session:
                session.close()
            raise DatabaseError(f"Failed to get agent stance for {owner_id} on {topic}: {e}") from e

    def get_world_knowledge(self, owner_id: str, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get world knowledge (facts from others) about a topic with sentiment.

        Args:
            owner_id (str): Owner/agent identifier
            topic (str): Topic to search for
            limit (int): Maximum number of results

        Returns:
            List[Dict[str, Any]]: List of edge dictionaries

        Raises:
            DatabaseError: If query fails
        """
        search_term = f"%{topic}%"

        try:
            session = self._get_new_session()
            
            # Get edges where source is not 'I' and target matches topic
            edges = session.query(Edge).filter(
                and_(
                    Edge.owner_id == owner_id,
                    Edge.source != 'I',
                    Edge.target.like(search_term)
                )
            ).limit(limit).all()
            
            session.close()
            
            # Convert to dictionaries
            return [
                {
                    "source": edge.source,
                    "relation": edge.relation,
                    "target": edge.target,
                    "sentiment": edge.sentiment,
                }
                for edge in edges
            ]
            
        except SQLAlchemyError as e:
            if session:
                session.close()
            raise DatabaseError(f"Failed to get world knowledge for {owner_id} on {topic}: {e}") from e

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
