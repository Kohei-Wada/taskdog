"""Factory for creating SQLite engines with optimized configuration.

This module provides a centralized way to create SQLAlchemy engines with
SQLite-specific optimizations. All repositories should use this factory
to share the same engine instance, avoiding redundant connection pools.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

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

    # Track migration status on engine to avoid running multiple times
    # when the same engine is reused or passed around
    if run_migration and not getattr(engine, "_migrations_completed", False):
        run_migrations(engine)
        engine._migrations_completed = True  # type: ignore[attr-defined]

    return engine


def create_session_factory(engine: Engine) -> "sessionmaker[Session]":
    """Create a sessionmaker bound to the given engine.

    Args:
        engine: SQLAlchemy Engine instance

    Returns:
        Configured sessionmaker for creating database sessions
    """
    return sessionmaker(bind=engine)  # type: ignore[return-value]
