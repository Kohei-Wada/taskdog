"""Audit log widget for displaying real-time audit logs in TUI.

This widget displays audit log entries in a side panel using Textual Static
widgets styled with CSS, showing operation details with timestamps, success
status, and client info.
"""

from typing import Any, ClassVar

from textual.containers import VerticalScroll
from textual.widgets import Static

from taskdog.tui.widgets.base_widget import TUIWidget
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog_core.application.dto.audit_log_dto import AuditLogOutput


class AuditLogWidget(VerticalScroll, ViNavigationMixin, TUIWidget):
    """A widget for displaying audit logs in a side panel.

    Features:
    - Displays recent audit log entries as styled Static widgets
    - Auto-updates when new logs are received
    - Supports scrolling with Vi-style bindings
    - Limited buffer to prevent memory issues
    """

    MAX_LOGS: ClassVar[int] = 50
    BINDINGS: ClassVar = ViNavigationMixin.VI_SCROLL_BINDINGS

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
        """Mount a log entry as a Static widget.

        Args:
            log: Audit log entry to display
            prepend: If True, insert at beginning; otherwise append
        """
        content = self._format_log_content(log)
        status_class = "log-success" if log.success else "log-error"
        widget = Static(content, classes=f"audit-log-entry {status_class}")

        if prepend and self._log_count > 0:
            self.mount(widget, before=0)
        else:
            self.mount(widget)
        self._log_count += 1

    def _format_log_content(self, log: AuditLogOutput) -> str:
        """Format log entry content as markup text.

        Args:
            log: Audit log entry to format

        Returns:
            Formatted markup string
        """
        lines: list[str] = []

        # Line 1: Timestamp and status
        ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        status = "[green]OK[/]" if log.success else "[red]ER[/]"
        lines.append(f"[dim]{ts}[/]  {status}")

        # Line 2: Operation
        lines.append(f"[cyan bold]{log.operation}[/]")

        # Line 3: Resource info (if exists)
        if log.resource_id or log.resource_name:
            parts: list[str] = []
            if log.resource_id:
                parts.append(f"[yellow]#{log.resource_id}[/]")
            if log.resource_name:
                name = (
                    log.resource_name[:30] + "..."
                    if len(log.resource_name) > 30
                    else log.resource_name
                )
                parts.append(name)
            lines.append(" ".join(parts))

        # Line 4: Client (if exists)
        if log.client_name:
            lines.append(f"[dim italic]@{log.client_name}[/]")

        return "\n".join(lines)

    def _trim_old_logs(self) -> None:
        """Remove old logs exceeding MAX_LOGS."""
        entries = list(self.query(".audit-log-entry"))
        if len(entries) > self.MAX_LOGS:
            for entry in entries[self.MAX_LOGS :]:
                entry.remove()
            self._log_count = self.MAX_LOGS

    @property
    def log_count(self) -> int:
        """Get the current number of logs."""
        return self._log_count
