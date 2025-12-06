"""Audit log controller for orchestrating audit log operations.

This controller provides a shared interface for audit log operations,
following Clean Architecture by ensuring all access to the audit log
repository goes through the application layer.
"""

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

    def log_operation(self, event: AuditEvent) -> None:
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
