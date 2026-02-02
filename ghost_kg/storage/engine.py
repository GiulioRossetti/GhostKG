"""
Database engine and session management for GhostKG.

Supports SQLite, PostgreSQL, and MySQL through SQLAlchemy.
"""

import os
from typing import Optional
from urllib.parse import urlparse
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from .models import Base
from ..utils.exceptions import DatabaseError


class DatabaseManager:
    """
    Manages database engine and session creation for multiple database backends.
    
    Supports:
    - SQLite (default): file path or ":memory:"
    - PostgreSQL: postgresql://user:password@host:port/dbname
    - MySQL: mysql+pymysql://user:password@host:port/dbname
    """
    
    def __init__(
        self,
        db_url: Optional[str] = None,
        db_path: Optional[str] = None,
        echo: bool = False,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: Optional[float] = None,
        pool_recycle: Optional[int] = None,
    ):
        """
        Initialize database manager.
        
        Args:
            db_url: SQLAlchemy database URL (e.g., postgresql://...)
                   Takes precedence over db_path
            db_path: Legacy SQLite file path (for backward compatibility)
            echo: Enable SQL query logging
            pool_size: Number of connections to maintain in the pool (PostgreSQL/MySQL only)
                      Default: 5
            max_overflow: Maximum overflow connections beyond pool_size (PostgreSQL/MySQL only)
                         Default: 10
            pool_timeout: Timeout for getting a connection from the pool (PostgreSQL/MySQL only)
                         Default: 30 seconds
            pool_recycle: Recycle connections after this many seconds (MySQL only recommended)
                         Default: 3600 (1 hour) for MySQL, None for PostgreSQL
        
        Raises:
            DatabaseError: If database connection fails
        """
        self.db_url = self._resolve_url(db_url, db_path)
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        
        self._initialize_engine()
    
    def _resolve_url(
        self, 
        db_url: Optional[str], 
        db_path: Optional[str]
    ) -> str:
        """
        Resolve database URL from various input formats.
        
        Priority:
        1. db_url (if provided)
        2. db_path (converted to SQLite URL)
        3. Default: agent_memory.db
        """
        if db_url:
            return db_url
        
        if db_path:
            # Convert file path to SQLite URL
            # Ensure absolute path for consistency
            if db_path != ":memory:":
                db_path = os.path.abspath(db_path)
            return f"sqlite:///{db_path}"
        
        # Default SQLite database
        return "sqlite:///agent_memory.db"
    
    def _initialize_engine(self):
        """
        Create SQLAlchemy engine with appropriate configuration.
        
        Raises:
            DatabaseError: If engine creation fails
        """
        try:
            parsed = urlparse(self.db_url)
            dialect = parsed.scheme.split("+")[0]
            
            # Engine configuration based on dialect
            engine_kwargs = {
                "echo": self.echo,
                "future": True,  # Use SQLAlchemy 2.0 style
            }
            
            if dialect == "sqlite":
                # SQLite-specific configuration
                engine_kwargs["connect_args"] = {"check_same_thread": False}
                
                # For in-memory databases, we MUST use StaticPool to maintain the same connection
                # Otherwise each query gets a new connection = new empty database
                if ":memory:" in self.db_url:
                    from sqlalchemy.pool import StaticPool
                    engine_kwargs["poolclass"] = StaticPool
                else:
                    engine_kwargs["poolclass"] = NullPool  # File-based SQLite doesn't need pooling
                
                # Enable foreign keys for SQLite
                @event.listens_for(Engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    if dialect == "sqlite":
                        cursor = dbapi_conn.cursor()
                        cursor.execute("PRAGMA foreign_keys=ON")
                        cursor.close()
            
            elif dialect == "postgresql":
                # PostgreSQL-specific configuration
                engine_kwargs["poolclass"] = QueuePool
                engine_kwargs["pool_size"] = self.pool_size if self.pool_size is not None else 5
                engine_kwargs["max_overflow"] = self.max_overflow if self.max_overflow is not None else 10
                engine_kwargs["pool_pre_ping"] = True  # Verify connections
                if self.pool_timeout is not None:
                    engine_kwargs["pool_timeout"] = self.pool_timeout
                if self.pool_recycle is not None:
                    engine_kwargs["pool_recycle"] = self.pool_recycle
            
            elif dialect == "mysql":
                # MySQL-specific configuration
                engine_kwargs["poolclass"] = QueuePool
                engine_kwargs["pool_size"] = self.pool_size if self.pool_size is not None else 5
                engine_kwargs["max_overflow"] = self.max_overflow if self.max_overflow is not None else 10
                engine_kwargs["pool_pre_ping"] = True
                # MySQL connections can go stale, so recycle them by default
                engine_kwargs["pool_recycle"] = self.pool_recycle if self.pool_recycle is not None else 3600
                if self.pool_timeout is not None:
                    engine_kwargs["pool_timeout"] = self.pool_timeout
            
            else:
                raise DatabaseError(
                    f"Unsupported database dialect: {dialect}. "
                    "Supported: sqlite, postgresql, mysql"
                )
            
            # Create engine
            self.engine = create_engine(self.db_url, **engine_kwargs)
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False,
            )
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database engine: {e}") from e
    
    def create_tables(self):
        """
        Create all tables defined in models if they don't exist.
        
        This is idempotent - safe to call multiple times.
        """
        try:
            Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            raise DatabaseError(f"Failed to create database tables: {e}") from e
    
    def get_session(self) -> Session:
        """
        Create a new database session.
        
        Returns:
            Session: SQLAlchemy session for database operations
        
        Usage:
            with manager.get_session() as session:
                # Use session
                session.commit()
        """
        if not self.SessionLocal:
            raise DatabaseError("Session factory not initialized")
        
        return self.SessionLocal()
    
    def dispose(self):
        """Close all database connections and dispose of the engine."""
        if self.engine:
            self.engine.dispose()
    
    @property
    def dialect_name(self) -> str:
        """Get the name of the database dialect (sqlite, postgresql, mysql)."""
        if self.engine:
            return self.engine.dialect.name
        return "unknown"
    
    def __repr__(self):
        return f"<DatabaseManager(dialect='{self.dialect_name}', url='{self.db_url}')>"
