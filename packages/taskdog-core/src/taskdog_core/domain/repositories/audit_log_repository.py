"""Abstract interface for audit log repository.

This interface defines the contract for managing audit logs,
abstracting away implementation details like database operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from taskdog_core.domain.entities.audit_log import AuditLog, AuditQuery


class AuditLogRepository(ABC):
    """Abstract interface for audit log persistence.

    This interface provides implementation-agnostic methods for audit log management.
    Implementation-specific methods (like clear/close for database cleanup)
    should be defined in concrete implementations.
    """

    @abstractmethod
    def save(self, log: AuditLog) -> None:
        """Persist an audit log record.

        Args:
            log: The audit log to save
        """

    @abstractmethod
    def get_logs(self, query: AuditQuery) -> list[AuditLog]:
        """Query audit logs with filtering and pagination.

        Args:
            query: Query parameters for filtering

        Returns:
            The matching audit logs (already ordered and paginated)
        """

    @abstractmethod
    def get_by_id(self, log_id: int) -> AuditLog | None:
        """Get a single audit log by ID.

        Args:
            log_id: The ID of the audit log to retrieve

        Returns:
            The audit log if found, None otherwise
        """

    @abstractmethod
    def count_logs(self, query: AuditQuery) -> int:
        """Count audit logs matching the query.

        Args:
            query: Query parameters for filtering

        Returns:
            Number of logs matching the query
        """

    @abstractmethod
    def get_deadline_changes(self, since: datetime | None = None) -> list[AuditLog]:
        """Get successful update_task logs whose deadline value changed.

        Includes initial settings (null to value) and removals (value to
        null) as well as reschedules (value to value).

        Args:
            since: Only include logs at or after this timestamp (None for all)

        Returns:
            The matching audit logs, oldest first
        """
