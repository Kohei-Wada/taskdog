"""SQLite-based repository for audit logs using SQLAlchemy.

This repository provides database persistence for audit logs using SQLite and
SQLAlchemy 2.0 ORM. It stores all API operations for accountability and review.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, delete, event, func, select
from sqlalchemy.orm import sessionmaker

from taskdog_core.application.dto.audit_log_dto import (
    AuditEvent,
    AuditLogListOutput,
    AuditLogOutput,
    AuditQuery,
)
from taskdog_core.infrastructure.persistence.database.models.audit_log_model import (
    AuditLogModel,
)
from taskdog_core.infrastructure.persistence.database.models.task_model import Base


class SqliteAuditLogRepository:
    """SQLite implementation of audit log repository using SQLAlchemy ORM.

    This repository:
    - Uses SQLite database for persistence
    - Provides ACID transaction guarantees
    - Implements connection pooling via SQLAlchemy engine
    - Supports filtering and pagination for log queries
    """

    def __init__(self, database_url: str):
        """Initialize the repository with a SQLite database.

        Args:
            database_url: SQLAlchemy database URL (e.g., "sqlite:///path/to/db.sqlite")
        """
        self.database_url = database_url

        # Create engine with SQLite-specific optimizations
        self.engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

        # Configure SQLite pragmas for concurrency
        @event.listens_for(self.engine, "connect")  # type: ignore[no-untyped-call]
        def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=30000")
                cursor.execute("PRAGMA synchronous=NORMAL")
            finally:
                cursor.close()

        # Create sessionmaker for managing database sessions
        self.Session = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

    def save(self, event: AuditEvent) -> None:
        """Persist an audit event to the database.

        Args:
            event: The audit event to save
        """
        with self.Session() as session:
            model = AuditLogModel(
                timestamp=event.timestamp,
                client_name=event.client_name,
                operation=event.operation,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                resource_name=event.resource_name,
                old_values=json.dumps(event.old_values) if event.old_values else None,
                new_values=json.dumps(event.new_values) if event.new_values else None,
                success=event.success,
                error_message=event.error_message,
            )
            session.add(model)
            session.commit()

    def get_logs(self, query: AuditQuery) -> AuditLogListOutput:
        """Query audit logs with filtering and pagination.

        Args:
            query: Query parameters for filtering

        Returns:
            AuditLogListOutput containing logs and pagination info
        """
        with self.Session() as session:
            # Build base query
            stmt = select(AuditLogModel)
            stmt = self._apply_filters(stmt, query)

            # Get total count before pagination
            count_stmt = select(func.count(AuditLogModel.id))
            count_stmt = self._apply_filters(count_stmt, query)
            total_count = session.scalar(count_stmt) or 0

            # Apply ordering and pagination
            stmt = stmt.order_by(AuditLogModel.timestamp.desc())  # type: ignore[attr-defined]
            stmt = stmt.offset(query.offset).limit(query.limit)

            # Execute query
            models = session.scalars(stmt).all()

            # Convert to output DTOs
            logs = [self._model_to_output(model) for model in models]

            return AuditLogListOutput(
                logs=logs,
                total_count=total_count,
                limit=query.limit,
                offset=query.offset,
            )

    def get_by_id(self, log_id: int) -> AuditLogOutput | None:
        """Get a single audit log by ID.

        Args:
            log_id: The ID of the audit log to retrieve

        Returns:
            The audit log if found, None otherwise
        """
        with self.Session() as session:
            model = session.get(AuditLogModel, log_id)
            if model is None:
                return None
            return self._model_to_output(model)

    def count_logs(self, query: AuditQuery) -> int:
        """Count audit logs matching the query.

        Args:
            query: Query parameters for filtering

        Returns:
            Number of logs matching the query
        """
        with self.Session() as session:
            stmt = select(func.count(AuditLogModel.id))
            stmt = self._apply_filters(stmt, query)
            return session.scalar(stmt) or 0

    def _apply_filters(self, stmt: Any, query: AuditQuery) -> Any:
        """Apply query filters to a SELECT statement.

        Args:
            stmt: The base SELECT statement
            query: Query parameters

        Returns:
            Modified SELECT statement with filters applied
        """
        if query.client_name is not None:
            stmt = stmt.where(AuditLogModel.client_name == query.client_name)

        if query.operation is not None:
            stmt = stmt.where(AuditLogModel.operation == query.operation)

        if query.resource_type is not None:
            stmt = stmt.where(AuditLogModel.resource_type == query.resource_type)

        if query.resource_id is not None:
            stmt = stmt.where(AuditLogModel.resource_id == query.resource_id)

        if query.success is not None:
            stmt = stmt.where(AuditLogModel.success == query.success)

        if query.start_date is not None:
            stmt = stmt.where(
                AuditLogModel.timestamp >= query.start_date  # type: ignore[operator]
            )

        if query.end_date is not None:
            stmt = stmt.where(
                AuditLogModel.timestamp <= query.end_date  # type: ignore[operator]
            )

        return stmt

    def _model_to_output(self, model: AuditLogModel) -> AuditLogOutput:
        """Convert an AuditLogModel to AuditLogOutput DTO.

        Args:
            model: The database model (must be a persisted model with all required fields)

        Returns:
            AuditLogOutput DTO
        """
        # These assertions ensure the model is a persisted instance with valid data
        assert model.id is not None
        assert model.timestamp is not None
        assert model.operation is not None
        assert model.resource_type is not None
        assert model.success is not None

        return AuditLogOutput(
            id=model.id,
            timestamp=model.timestamp,
            client_name=model.client_name,
            operation=model.operation,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            resource_name=model.resource_name,
            old_values=json.loads(model.old_values) if model.old_values else None,
            new_values=json.loads(model.new_values) if model.new_values else None,
            success=model.success,
            error_message=model.error_message,
        )

    def clear(self) -> None:
        """Delete all audit logs from the database.

        This method is primarily intended for testing purposes.
        """
        with self.Session() as session:
            session.execute(delete(AuditLogModel))
            session.commit()

    def close(self) -> None:
        """Close database connections and clean up resources."""
        self.engine.dispose()
