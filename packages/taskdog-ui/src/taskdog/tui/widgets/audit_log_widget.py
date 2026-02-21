"""Audit log widget for displaying real-time audit logs in TUI.

This widget displays audit log entries in a side panel using Textual
widgets styled with CSS, showing operation details with timestamps, success
status, and client info.
"""

from typing import Any, ClassVar

from textual.binding import Binding
from textual.containers import VerticalScroll

from taskdog.tui.widgets.audit_log_entry_builder import create_audit_entry_widget
from taskdog.tui.widgets.base_widget import TUIWidget
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog_core.application.dto.audit_log_dto import AuditLogOutput


class AuditLogWidget(VerticalScroll, ViNavigationMixin, TUIWidget):
    """A widget for displaying audit logs in a side panel.

    Features:
    - Displays recent audit log entries as styled widgets
    - Auto-updates when new logs are received
    - Supports scrolling with Vi-style bindings
    - Limited buffer to prevent memory issues
    - Theme-aware colors via CSS classes
    """

    MAX_LOGS: ClassVar[int] = 50
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = list(
        ViNavigationMixin.VI_SCROLL_BINDINGS
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the audit log widget."""
        super().__init__(*args, **kwargs)
        self.can_focus = True
        self._log_count = 0

    def load_logs(self, logs: list[AuditLogOutput]) -> None:
        """Load logs from API response.

        Args:
            logs: List of audit log entries (newest first from API)
        """
        self.clear_logs()
        for log in logs:
            self._mount_log_entry(log)

    def add_log(self, log: AuditLogOutput) -> None:
        """Add a new log entry at the beginning.

        Args:
            log: New audit log entry
        """
        self._mount_log_entry(log, prepend=True)
        self._trim_old_logs()

    def clear_logs(self) -> None:
        """Clear all logs from the widget."""
        self.query(".audit-log-entry").remove()
        self._log_count = 0

    def _mount_log_entry(self, log: AuditLogOutput, prepend: bool = False) -> None:
        """Mount a log entry as a container with styled widgets.

        Args:
            log: Audit log entry to display
            prepend: If True, insert at beginning; otherwise append
        """
        entry = create_audit_entry_widget(log)

        if prepend and self._log_count > 0:
            self.mount(entry, before=0)
        else:
            self.mount(entry)
        self._log_count += 1

    def _trim_old_logs(self) -> None:
        """Remove old logs exceeding MAX_LOGS."""
        entries = list(self.query(".audit-log-entry"))
        if len(entries) > self.MAX_LOGS:
            for entry in entries[self.MAX_LOGS :]:
                entry.remove()
            self._log_count = len(self.query(".audit-log-entry"))

    @property
    def log_count(self) -> int:
        """Get the current number of logs."""
        return self._log_count
