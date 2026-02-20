"""Base repository class for SQLite-based repositories.

Provides shared engine management and session factory initialization
used by all SQLite repository implementations.
"""

from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from taskdog_core.infrastructure.persistence.database.engine_factory import (
    create_session_factory,
    create_sqlite_engine,
)


class SqliteBaseRepository:
    """Base class for SQLite repositories with shared engine lifecycle.

    Handles:
    - Engine creation or reuse (via ``engine`` parameter)
    - Session factory (``self.Session``) creation
    - Engine disposal on ``close()`` when the repository owns the engine
    """

    def __init__(self, database_url: str, engine: Engine | None = None) -> None:
        self.database_url = database_url

        # Use provided engine or create a new one
        self._owns_engine = engine is None
        self.engine: Engine = (
            engine if engine is not None else create_sqlite_engine(database_url)
        )

        # Create sessionmaker for managing database sessions
        self.Session: sessionmaker = create_session_factory(self.engine)

    def close(self) -> None:
        """Close database connections and clean up resources.

        Only disposes the engine if this repository created it.
        """
        if self._owns_engine:
            self.engine.dispose()
