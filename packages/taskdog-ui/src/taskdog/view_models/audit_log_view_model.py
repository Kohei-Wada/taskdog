"""ViewModels for audit log presentation.

These ViewModels hold presentation-ready audit log data without domain
entities or rendering-technology dependencies (no Rich, no Textual). Width
truncation and coloring are applied by the renderers/widgets that consume them.
"""

from dataclasses import dataclass
from datetime import datetime

from taskdog.view_models.base import BaseViewModel


@dataclass(frozen=True)
class AuditChangeViewModel(BaseViewModel):
    """A single changed field in an audit log entry.

    ``old`` and ``new`` are already value-formatted strings (e.g. ``∅`` for
    None, ``✓``/``✗`` for booleans, long strings truncated).
    """

    key: str
    old: str
    new: str


@dataclass(frozen=True)
class AuditLogRowViewModel(BaseViewModel):
    """A single audit log entry, presentation-ready."""

    id: int
    timestamp: datetime
    operation: str
    client_name: str | None
    resource_id: int | None
    resource_name: str | None
    success: bool
    error_message: str | None
    changes: tuple[AuditChangeViewModel, ...]


@dataclass(frozen=True)
class AuditLogViewModel(BaseViewModel):
    """A page of audit log entries."""

    rows: tuple[AuditLogRowViewModel, ...]
    total_count: int
