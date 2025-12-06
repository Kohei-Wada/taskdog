"""Audit log controller for orchestrating audit log operations.

This controller provides a shared interface for audit log operations,
following Clean Architecture by ensuring all access to the audit log
repository goes through the application layer.
"""

from datetime import datetime
from typing import Any

from taskdog_core.application.dto.audit_log_dto import (
    AuditEvent,
    AuditLogListOutput,
    AuditLogOutput,
    AuditQuery,
)
from taskdog_core.domain.services.logger import Logger
from taskdog_core.infrastructure.persistence.database.sqlite_audit_log_repository import (
    SqliteAuditLogRepository,
)


class AuditLogController:
    """Controller for audit log operations.

    This class orchestrates audit log operations, providing a consistent
    interface for saving and querying audit logs. Presentation layers
    (API server) should use this controller rather than accessing the
    repository directly.

    Attributes:
        repository: Audit log repository for data persistence
        logger: Logger for operation tracking
    """

    def __init__(
        self,
        repository: SqliteAuditLogRepository,
        logger: Logger,
    ) -> None:
        """Initialize the audit log controller.

        Args:
            repository: Audit log repository for persistence
            logger: Logger for tracking operations
        """
        self._repository = repository
        self._logger = logger

    def save(self, event: AuditEvent) -> None:
        """Save an audit event to the database.

        Args:
            event: The audit event to save
        """
        self._repository.save(event)
        self._logger.debug(
            f"Audit log saved: operation={event.operation}, "
            f"resource_type={event.resource_type}, "
            f"resource_id={event.resource_id}"
        )

    def log_operation(
        self,
        *,
        operation: str,
        resource_type: str,
        success: bool,
        client_name: str | None = None,
        resource_id: int | None = None,
        resource_name: str | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """Log an operation with a convenience method.

        This is a shortcut for creating an AuditEvent and calling save().

        Args:
            operation: The operation type (e.g., 'create_task')
            resource_type: The resource type (e.g., 'task')
            success: Whether the operation succeeded
            client_name: The authenticated client name
            resource_id: The resource ID (task ID, etc.)
            resource_name: The resource name (task name, etc.)
            old_values: Values before the change
            new_values: Values after the change
            error_message: Error message if the operation failed
        """
        event = AuditEvent(
            timestamp=datetime.now(),
            operation=operation,
            resource_type=resource_type,
            success=success,
            client_name=client_name,
            resource_id=resource_id,
            resource_name=resource_name,
            old_values=old_values,
            new_values=new_values,
            error_message=error_message,
        )
        self.save(event)

    def get_logs(self, query: AuditQuery) -> AuditLogListOutput:
        """Query audit logs with filtering and pagination.

        Args:
            query: Query parameters for filtering

        Returns:
            AuditLogListOutput containing logs and pagination info
        """
        return self._repository.get_logs(query)

    def get_by_id(self, log_id: int) -> AuditLogOutput | None:
        """Get a single audit log by ID.

        Args:
            log_id: The ID of the audit log to retrieve

        Returns:
            AuditLogOutput if found, None otherwise
        """
        return self._repository.get_by_id(log_id)

    def count_logs(self, query: AuditQuery) -> int:
        """Count audit logs matching the query.

        Args:
            query: Query parameters for filtering

        Returns:
            Number of logs matching the query
        """
        return self._repository.count_logs(query)
