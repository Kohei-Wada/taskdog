"""DTOs for audit logging operations.

This module defines data transfer objects for audit log operations,
including the audit event structure and query parameters.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    """Represents a single audit log event.

    This DTO is used to capture audit information when API operations
    are performed. It tracks who did what, when, and what changed.
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


@dataclass(frozen=True)
class AuditQuery:
    """Query parameters for filtering audit logs.

    All fields are optional. If not specified, no filtering is applied
    for that field.
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
