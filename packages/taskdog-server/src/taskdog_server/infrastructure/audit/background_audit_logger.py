"""Background audit logger for non-blocking audit log persistence.

This module provides a non-blocking audit logger that schedules log writes
as FastAPI background tasks, ensuring API responses are not delayed.
"""

from datetime import datetime
from typing import Any

from fastapi import BackgroundTasks

from taskdog_core.application.dto.audit_log_dto import AuditEvent
from taskdog_core.infrastructure.persistence.database.sqlite_audit_log_repository import (
    SqliteAuditLogRepository,
)


class BackgroundAuditLogger:
    """Non-blocking audit logger using FastAPI background tasks.

    Schedules audit log writes as background tasks to avoid blocking
    API responses. This is particularly important for high-throughput
    scenarios where logging should not impact response times.
    """

    def __init__(
        self,
        repository: SqliteAuditLogRepository,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Initialize the background audit logger.

        Args:
            repository: The audit log repository for persistence
            background_tasks: FastAPI background tasks for async scheduling
        """
        self._repository = repository
        self._background_tasks = background_tasks

    def log(self, event: AuditEvent) -> None:
        """Schedule an audit event to be logged in the background.

        Args:
            event: The audit event to log
        """
        self._background_tasks.add_task(self._repository.save, event)

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

        This is a shortcut for creating an AuditEvent and calling log().

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
        self.log(event)
