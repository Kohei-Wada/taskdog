"""Audit log widget for displaying real-time audit logs in TUI.

This widget displays audit log entries in a side panel as cards,
showing operation details with timestamps, success status, and client info.
"""

from collections import deque
from typing import Any, ClassVar

from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Static

from taskdog.tui.widgets.base_widget import TUIWidget
from taskdog_core.application.dto.audit_log_dto import AuditLogOutput


class AuditLogWidget(VerticalScroll, TUIWidget):
    """A widget for displaying audit logs in a side panel.

    Features:
    - Displays recent audit log entries
    - Auto-updates when new logs are received
    - Supports scrolling with Vi-style bindings
    - Limited buffer to prevent memory issues
    """

    MAX_LOGS: ClassVar[int] = 50

    BINDINGS: ClassVar = [
        Binding(
            "j",
            "scroll_down",
            "Scroll Down",
            show=False,
            tooltip="Scroll down one line (Vi-style)",
        ),
        Binding(
            "k",
            "scroll_up",
            "Scroll Up",
            show=False,
            tooltip="Scroll up one line (Vi-style)",
        ),
        Binding(
            "g",
            "scroll_home",
            "Top",
            show=False,
            tooltip="Scroll to top (Vi-style)",
        ),
        Binding(
            "G",
            "scroll_end",
            "Bottom",
            show=False,
            tooltip="Scroll to bottom (Vi-style)",
        ),
        Binding(
            "ctrl+d",
            "page_down",
            "Page Down",
            show=False,
            tooltip="Scroll down half a page",
        ),
        Binding(
            "ctrl+u",
            "page_up",
            "Page Up",
            show=False,
            tooltip="Scroll up half a page",
        ),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the audit log widget."""
        super().__init__(*args, **kwargs)
        self.can_focus = True
        self._logs: deque[AuditLogOutput] = deque(maxlen=self.MAX_LOGS)
        self._content_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        self._content_widget = Static("", id="audit-logs-content")
        yield self._content_widget

    def load_logs(self, logs: list[AuditLogOutput]) -> None:
        """Load logs from API response.

        Args:
            logs: List of audit log entries (newest first from API)
        """
        self._logs.clear()
        for log in logs:
            self._logs.append(log)
        self._render_logs()

    def add_log(self, log: AuditLogOutput) -> None:
        """Add a new log entry at the beginning.

        Args:
            log: New audit log entry
        """
        self._logs.appendleft(log)
        self._render_logs()

    def clear_logs(self) -> None:
        """Clear all logs from the widget."""
        self._logs.clear()
        self._render_logs()

    def _render_logs(self) -> None:
        """Render all logs as cards."""
        if not self._content_widget:
            return

        if not self._logs:
            self._content_widget.update("[dim]No audit logs available[/dim]")
            return

        cards = [self._format_log_card(log) for log in self._logs]
        self._content_widget.update(Group(*cards))

    def _format_log_card(self, log: AuditLogOutput) -> Panel:
        """Format a single log entry as a card.

        Args:
            log: Audit log entry to format

        Returns:
            Rich Panel representing the log entry
        """
        # Status and border color
        if log.success:
            status_icon = "[green]OK[/green]"
            border_style = "green"
        else:
            status_icon = "[red]ER[/red]"
            border_style = "red"

        # Build card content
        lines: list[Text] = []

        # Line 1: Timestamp and status
        ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        line1 = Text()
        line1.append(ts, style="dim")
        line1.append("  ")
        line1.append_text(Text.from_markup(status_icon))
        lines.append(line1)

        # Line 2: Operation
        line2 = Text()
        line2.append(log.operation, style="cyan bold")
        lines.append(line2)

        # Line 3: Resource info (if exists)
        if log.resource_id or log.resource_name:
            line3 = Text()
            if log.resource_id:
                line3.append(f"#{log.resource_id}", style="yellow")
            if log.resource_name:
                if log.resource_id:
                    line3.append(" ")
                name = (
                    log.resource_name[:30] + "..."
                    if len(log.resource_name) > 30
                    else log.resource_name
                )
                line3.append(name)
            lines.append(line3)

        # Line 4: Client (if exists)
        if log.client_name:
            line4 = Text()
            line4.append(f"@{log.client_name}", style="dim italic")
            lines.append(line4)

        # Combine lines
        content = Text("\n").join(lines)

        return Panel(
            content,
            border_style=border_style,
            padding=(0, 1),
        )

    @property
    def log_count(self) -> int:
        """Get the current number of logs.

        Returns:
            Number of logs currently in the widget
        """
        return len(self._logs)
