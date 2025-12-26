"""Alembic environment configuration for taskdog-core.

This file configures how Alembic runs migrations. It supports both
offline (SQL script generation) and online (direct database connection) modes.

The online mode is optimized for programmatic use via migration_runner.py,
which passes an existing engine through config.attributes["connection"].
This is necessary for in-memory SQLite databases where new connections
create separate databases.
"""

from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Engine

from taskdog_core.infrastructure.persistence.database.models.task_model import Base

# This is the Alembic Config object, which provides access to values
# within the .ini file (or programmatic config) in use.
config = context.config

# Set target metadata from existing SQLAlchemy Base
# This includes all models: TaskModel, TagModel, TaskTagModel, AuditLogModel
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    This mode supports two scenarios:
    1. Programmatic use via migration_runner.py - uses existing engine from
       config.attributes["connection"] (required for in-memory SQLite)
    2. CLI use - creates a new engine from config URL
    """
    # Check if an engine was passed through config attributes
    # This is set by migration_runner.py for programmatic use
    connectable: Engine | Any = config.attributes.get("connection", None)

    if connectable is None:
        # CLI mode: create a new engine from config
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    # Use the engine to run migrations
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
