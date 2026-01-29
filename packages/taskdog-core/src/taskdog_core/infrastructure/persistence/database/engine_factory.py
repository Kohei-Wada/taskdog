"""Factory for creating SQLite engines with optimized configuration.

This module provides a centralized way to create SQLAlchemy engines with
SQLite-specific optimizations. All repositories should use this factory
to share the same engine instance, avoiding redundant connection pools.
"""

from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from taskdog_core.infrastructure.persistence.database.migration_runner import (
    run_migrations,
)


def create_sqlite_engine(database_url: str, run_migration: bool = True) -> Engine:
    """Create a SQLAlchemy engine with SQLite-specific optimizations.

    This function creates an engine configured for:
    - WAL mode for concurrent reads during writes
    - 30 second busy timeout for lock acquisition
    - NORMAL synchronous mode for balanced safety/performance

    Args:
        database_url: SQLAlchemy database URL (e.g., "sqlite:///path/to/db.sqlite")
        run_migration: Whether to run database migrations (default: True)

    Returns:
        Configured SQLAlchemy Engine instance
    """
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")  # type: ignore[no-untyped-call]
    def set_sqlite_pragma(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA synchronous=NORMAL")
        finally:
            cursor.close()

    if run_migration:
        run_migrations(engine)

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a sessionmaker bound to the given engine.

    Args:
        engine: SQLAlchemy Engine instance

    Returns:
        Configured sessionmaker for creating database sessions
    """
    return sessionmaker(bind=engine)
