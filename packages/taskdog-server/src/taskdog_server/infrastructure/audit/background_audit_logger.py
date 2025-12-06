"""Background audit logger for non-blocking audit log persistence.

This module provides a non-blocking audit logger that schedules log writes
as FastAPI background tasks, ensuring API responses are not delayed.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import BackgroundTasks

from taskdog_core.application.dto.audit_log_dto import AuditEvent
from taskdog_core.controllers.audit_log_controller import AuditLogController

logger = logging.getLogger(__name__)


class BackgroundAuditLogger:
    """Non-blocking audit logger using FastAPI background tasks.

    Schedules audit log writes as background tasks to avoid blocking
    API responses. This is particularly important for high-throughput
    scenarios where logging should not impact response times.
    """

    def __init__(
        self,
        controller: AuditLogController,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Initialize the background audit logger.

        Args:
            controller: The audit log controller for persistence
            background_tasks: FastAPI background tasks for async scheduling
        """
        self._controller = controller
        self._background_tasks = background_tasks

    def _save_with_error_handling(self, event: AuditEvent) -> None:
        """Save an audit event with error handling.

        This method wraps the controller log operation to catch and log
        any errors that occur during persistence, preventing silent failures.

        Args:
            event: The audit event to save
        """
        try:
            self._controller.log_operation(event)
        except Exception as e:
            # Log the failure but don't propagate - audit logging should not
            # cause API failures
            logger.error(
                "Failed to save audit log: operation=%s, resource_type=%s, "
                "resource_id=%s, error=%s",
                event.operation,
                event.resource_type,
                event.resource_id,
                str(e),
            )

    def log(self, event: AuditEvent) -> None:
        """Schedule an audit event to be logged in the background.

        Args:
            event: The audit event to log
        """
        self._background_tasks.add_task(self._save_with_error_handling, event)

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
