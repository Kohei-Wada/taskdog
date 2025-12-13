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

        # Line 2: Operation (no color - main content should be readable without distraction)
        lines.append(log.operation)

        # Line 3: Resource info (if exists)
        if log.resource_id or log.resource_name:
            parts: list[str] = []
            if log.resource_id:
                parts.append(f"[dim]#{log.resource_id}[/]")
            if log.resource_name:
                name = (
                    log.resource_name[:30] + "..."
                    if len(log.resource_name) > 30
                    else log.resource_name
                )
                parts.append(name)
            lines.append(" ".join(parts))

        # Line 4: Changes (if exists) - show what changed
        changes = self._format_changes(log.old_values, log.new_values)
        if changes:
            lines.append(f"[dim]{changes}[/]")

        # Line 5: Error message (if failed)
        if not log.success and log.error_message:
            error_msg = (
                log.error_message[:40] + "..."
                if len(log.error_message) > 40
                else log.error_message
            )
            lines.append(f"[red]{error_msg}[/]")

        # Line 6: Client (if exists) - highlight with cyan (secondary-like color)
        if log.client_name:
            lines.append(f"[cyan]@{log.client_name}[/]")

        return "\n".join(lines)

    def _format_changes(
        self,
        old_values: dict[str, Any] | None,
        new_values: dict[str, Any] | None,
    ) -> str:
        """Format changes between old and new values.

        Args:
            old_values: Values before the change
            new_values: Values after the change

        Returns:
            Formatted change string (e.g., "priority: 3 → 5")
        """
        if not old_values and not new_values:
            return ""

        changes: list[str] = []

        # Get all keys that changed
        all_keys: set[str] = set()
        if old_values:
            all_keys.update(old_values.keys())
        if new_values:
            all_keys.update(new_values.keys())

        for key in sorted(all_keys):
            old_val = old_values.get(key) if old_values else None
            new_val = new_values.get(key) if new_values else None

            if old_val != new_val:
                old_str = self._format_value(old_val)
                new_str = self._format_value(new_val)
                changes.append(f"{key}: {old_str} → {new_str}")

        # Limit to 2 changes to keep it compact
        if len(changes) > 2:
            return ", ".join(changes[:2]) + f" (+{len(changes) - 2})"
        return ", ".join(changes)

    def _format_value(self, value: Any) -> str:
        """Format a single value for display.

        Args:
            value: Value to format

        Returns:
            Formatted string representation
        """
        if value is None:
            return "∅"
        if isinstance(value, bool):
            return "✓" if value else "✗"
        if isinstance(value, str) and len(value) > 15:
            return value[:15] + "..."
        return str(value)

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
