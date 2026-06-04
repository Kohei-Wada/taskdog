"""Output DTOs for audit logging operations.

These are the presentation-facing representations of audit logs returned by the
application layer. The domain types (``AuditLog`` entity and ``AuditQuery``)
live in ``domain/entities/audit_log.py``.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from taskdog_core.domain.entities.audit_log import AuditLog


@dataclass(frozen=True)
class AuditLogOutput:
    """Output DTO for a single audit log entry."""

    id: int
    """Unique identifier for the audit log entry."""

    timestamp: datetime
    """When the operation occurred."""

    client_name: str | None
    """The authenticated client name."""

    operation: str
    """The type of operation."""

    resource_type: str
    """The type of resource."""

    resource_id: int | None
    """The ID of the affected resource."""

    resource_name: str | None
    """The name of the affected resource."""

    old_values: dict[str, Any] | None
    """Values before the change."""

    new_values: dict[str, Any] | None
    """Values after the change."""

    success: bool
    """Whether the operation succeeded."""

    error_message: str | None
    """Error message if the operation failed."""

    @classmethod
    def from_entity(cls, log: AuditLog) -> "AuditLogOutput":
        """Build an output DTO from a persisted ``AuditLog`` entity."""
        assert log.id is not None, "cannot build output DTO from an unpersisted log"
        return cls(
            id=log.id,
            timestamp=log.timestamp,
            client_name=log.client_name,
            operation=log.operation,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            resource_name=log.resource_name,
            old_values=log.old_values,
            new_values=log.new_values,
            success=log.success,
            error_message=log.error_message,
        )


@dataclass(frozen=True)
class AuditLogListOutput:
    """Output DTO for audit log list with pagination info."""

    logs: list[AuditLogOutput] = field(default_factory=list)
    """List of audit log entries."""

    total_count: int = 0
    """Total number of logs matching the query (for pagination)."""

    limit: int = 100
    """Maximum number of logs returned."""

    offset: int = 0
    """Number of logs skipped."""
