"""Abstract interface for audit log repository.

This interface defines the contract for managing audit logs,
abstracting away implementation details like database operations.
"""

from abc import ABC, abstractmethod

from taskdog_core.application.dto.audit_log_dto import (
    AuditEvent,
    AuditLogListOutput,
    AuditLogOutput,
    AuditQuery,
)


class AuditLogRepository(ABC):
    """Abstract interface for audit log persistence.

    This interface provides implementation-agnostic methods for audit log management.
    Implementation-specific methods (like clear/close for database cleanup)
    should be defined in concrete implementations.
    """

    @abstractmethod
    def save(self, event: AuditEvent) -> None:
        """Persist an audit event.

        Args:
            event: The audit event to save
        """
        pass

    @abstractmethod
    def get_logs(self, query: AuditQuery) -> AuditLogListOutput:
        """Query audit logs with filtering and pagination.

        Args:
            query: Query parameters for filtering

        Returns:
            AuditLogListOutput containing logs and pagination info
        """
        pass

    @abstractmethod
    def get_by_id(self, log_id: int) -> AuditLogOutput | None:
        """Get a single audit log by ID.

        Args:
            log_id: The ID of the audit log to retrieve

        Returns:
            The audit log if found, None otherwise
        """
        pass

    @abstractmethod
    def count_logs(self, query: AuditQuery) -> int:
        """Count audit logs matching the query.

        Args:
            query: Query parameters for filtering

        Returns:
            Number of logs matching the query
        """
        pass
