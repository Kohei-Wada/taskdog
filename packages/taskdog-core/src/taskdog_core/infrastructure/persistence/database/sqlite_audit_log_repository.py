"""SQLite-based repository for audit logs using SQLAlchemy.

This repository provides database persistence for audit logs using SQLite and
SQLAlchemy 2.0 ORM. It stores all API operations for accountability and review.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, func, select

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

from taskdog_core.domain.entities.audit_log import AuditLog, AuditQuery
from taskdog_core.domain.repositories.audit_log_repository import AuditLogRepository
from taskdog_core.infrastructure.persistence.database.base_repository import (
    SqliteBaseRepository,
)
from taskdog_core.infrastructure.persistence.database.models.audit_log_model import (
    AuditLogModel,
)


class SqliteAuditLogRepository(SqliteBaseRepository, AuditLogRepository):
    """SQLite implementation of audit log repository using SQLAlchemy ORM.

    This repository:
    - Uses SQLite database for persistence
    - Provides ACID transaction guarantees
    - Implements connection pooling via SQLAlchemy engine
    - Supports filtering and pagination for log queries
    """

    def __init__(self, database_url: str, engine: Engine | None = None):
        """Initialize the repository with a SQLite database.

        Args:
            database_url: SQLAlchemy database URL (e.g., "sqlite:///path/to/db.sqlite")
            engine: SQLAlchemy Engine instance. If None, creates a new engine.
                   Pass a shared engine to avoid redundant connection pools.
        """
        super().__init__(database_url, engine)

    def save(self, log: AuditLog) -> None:
        """Persist an audit log record to the database.

        Args:
            log: The audit log to save
        """
        with self.Session() as session:
            model = AuditLogModel(
                timestamp=log.timestamp,
                client_name=log.client_name,
                operation=log.operation,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                resource_name=log.resource_name,
                old_values=json.dumps(log.old_values) if log.old_values else None,
                new_values=json.dumps(log.new_values) if log.new_values else None,
                success=log.success,
                error_message=log.error_message,
            )
            session.add(model)
            session.commit()

    def get_logs(self, query: AuditQuery) -> list[AuditLog]:
        """Query audit logs with filtering and pagination.

        Args:
            query: Query parameters for filtering

        Returns:
            The matching audit logs, newest first
        """
        with self.Session() as session:
            stmt = select(AuditLogModel)
            stmt = self._apply_filters(stmt, query)
            stmt = stmt.order_by(AuditLogModel.timestamp.desc())  # type: ignore[attr-defined]
            stmt = stmt.offset(query.offset).limit(query.limit)

            models = session.scalars(stmt).all()
            return [self._model_to_entity(model) for model in models]

    def get_by_id(self, log_id: int) -> AuditLog | None:
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
            return self._model_to_entity(model)

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

    def _model_to_entity(self, model: AuditLogModel) -> AuditLog:
        """Convert an AuditLogModel to an AuditLog domain entity.

        Args:
            model: The database model (must be a persisted model with all required fields)

        Returns:
            AuditLog entity
        """
        # These assertions ensure the model is a persisted instance with valid data
        assert model.id is not None
        assert model.timestamp is not None
        assert model.operation is not None
        assert model.resource_type is not None
        assert model.success is not None

        # Parse JSON values with error handling for malformed data
        try:
            old_values = json.loads(model.old_values) if model.old_values else None
        except json.JSONDecodeError:
            old_values = None

        try:
            new_values = json.loads(model.new_values) if model.new_values else None
        except json.JSONDecodeError:
            new_values = None

        return AuditLog(
            id=model.id,
            timestamp=model.timestamp,
            client_name=model.client_name,
            operation=model.operation,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            resource_name=model.resource_name,
            old_values=old_values,
            new_values=new_values,
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
