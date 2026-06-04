"""Audit log domain entity and query value object.

An audit log records who did what, when, and what changed. These are pure
domain types with no framework or application-layer dependencies, so the
repository interface can speak in domain terms (see
``domain/repositories/audit_log_repository.py``). The application layer maps
``AuditLog`` to its output DTOs.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AuditLog:
    """A single audit log record.

    ``id`` is ``None`` before the record is persisted and set once the
    repository has stored it.

    Audit records are deliberately not validated in ``__post_init__``: failing
    to construct one would drop an entry from the audit trail, which is worse
    than recording an imperfect one.
    """

    timestamp: datetime
    """When the operation occurred."""

    operation: str
    """The type of operation (e.g., 'create_task', 'complete_task')."""

    resource_type: str
    """The type of resource (e.g., 'task', 'schedule')."""

    success: bool
    """Whether the operation succeeded."""

    client_name: str | None = None
    """The authenticated client name (e.g., 'claude-code')."""

    resource_id: int | None = None
    """The ID of the affected resource (task ID, etc.)."""

    resource_name: str | None = None
    """The name of the affected resource (task name, etc.)."""

    old_values: dict[str, Any] | None = None
    """Values before the change (for update operations)."""

    new_values: dict[str, Any] | None = None
    """Values after the change."""

    error_message: str | None = None
    """Error message if the operation failed."""

    id: int | None = None
    """Unique identifier, assigned by the repository on persistence."""


@dataclass(frozen=True)
class AuditQuery:
    """Query parameters for filtering audit logs.

    All fields are optional. If not specified, no filtering is applied for
    that field. This is a repository query value object, not persistence- or
    presentation-specific.
    """

    client_name: str | None = None
    """Filter by client name."""

    operation: str | None = None
    """Filter by operation type."""

    resource_type: str | None = None
    """Filter by resource type."""

    resource_id: int | None = None
    """Filter by resource ID (task ID)."""

    success: bool | None = None
    """Filter by success status."""

    start_date: datetime | None = None
    """Filter logs from this date onwards."""

    end_date: datetime | None = None
    """Filter logs up to this date."""

    limit: int = 100
    """Maximum number of logs to return."""

    offset: int = 0
    """Number of logs to skip (for pagination)."""
