"""Programmatic migration runner for taskdog database.

This module provides a simple interface to run Alembic migrations
without needing the alembic CLI. It's designed to be called during
application startup.
"""

from __future__ import annotations

import threading
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

# Lock for thread-safe migration execution
_migration_lock = threading.Lock()


def get_migrations_dir() -> Path:
    """Get the path to the migrations directory."""
    return Path(__file__).parent / "migrations"


def create_alembic_config(engine: Engine) -> AlembicConfig:
    """Create an Alembic Config object programmatically.

    Args:
        engine: SQLAlchemy Engine instance

    Returns:
        Configured AlembicConfig instance with engine attached
    """
    migrations_dir = get_migrations_dir()

    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))

    # Pass the engine through config attributes for env.py to use
    # This is necessary for in-memory SQLite databases where new connections
    # create separate databases
    alembic_cfg.attributes["connection"] = engine

    return alembic_cfg


def _get_head_revision(alembic_cfg: AlembicConfig) -> str | None:
    """Get the head revision from the migration scripts.

    Args:
        alembic_cfg: Alembic configuration

    Returns:
        The head revision identifier or None if no revisions exist
    """
    script = ScriptDirectory.from_config(alembic_cfg)
    head: str | None = script.get_current_head()
    return head


def run_migrations(engine: Engine) -> None:
    """Run all pending database migrations.

    This function should be called during application startup to ensure
    the database schema is up to date.

    For existing databases without alembic_version table, it stamps the
    database with the initial revision to bring it under version control.

    This function is thread-safe and will skip if already at head revision.

    Args:
        engine: SQLAlchemy Engine instance
    """
    alembic_cfg = create_alembic_config(engine)

    # Check if this is an existing database without migration tracking
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    has_alembic_version = "alembic_version" in existing_tables
    has_existing_data = "tasks" in existing_tables

    # If already at head revision, skip migration
    if has_alembic_version:
        current = get_current_revision(engine)
        head = _get_head_revision(alembic_cfg)
        if current == head:
            return

    # Use lock for thread-safe migration execution
    # This prevents Alembic's global state from being corrupted by concurrent access
    with _migration_lock:
        # Re-check after acquiring lock (another thread might have run migrations)
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        has_alembic_version = "alembic_version" in existing_tables

        if has_alembic_version:
            current = get_current_revision(engine)
            head = _get_head_revision(alembic_cfg)
            if current == head:
                return

        if has_existing_data and not has_alembic_version:
            # Existing database without migrations - stamp with initial revision
            # This marks the DB as already at the initial schema
            command.stamp(alembic_cfg, "001_initial")

        # Run any pending migrations
        command.upgrade(alembic_cfg, "head")


def get_current_revision(engine: Engine) -> str | None:
    """Get the current database revision.

    Args:
        engine: SQLAlchemy Engine instance

    Returns:
        Current revision string or None if not versioned
    """
    inspector = inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        return None

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()
        return row[0] if row else None
