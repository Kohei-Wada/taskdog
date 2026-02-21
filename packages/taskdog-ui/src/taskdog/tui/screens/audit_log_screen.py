"""Audit log screen for TUI - full-page audit log display."""

from typing import ClassVar

from rich.text import Text
from taskdog_client import TaskdogApiClient
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Header

from taskdog.tui.widgets.audit_log_entry_builder import (
    format_audit_changes,
)
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog_core.application.dto.audit_log_dto import AuditLogOutput

MAX_RESOURCE_NAME_LENGTH = 25


class AuditLogScreen(Screen[None], ViNavigationMixin):
    """Full-page screen for displaying audit log entries.

    Shows all audit log columns in a full-width DataTable:
    Timestamp, ID, Name, Operation, Changes, Client, Status.
    """

    BINDINGS: ClassVar = [
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        Binding("q", "pop_screen", "Back", show=True),
        Binding("escape", "pop_screen", "Back", show=False),
    ]

    def __init__(self, api_client: TaskdogApiClient) -> None:
        """Initialize the audit log screen.

        Args:
            api_client: API client for fetching audit logs
        """
        super().__init__()
        self._api_client = api_client

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header(show_clock=True)
        table: DataTable = DataTable(id="audit-log-table")  # type: ignore[type-arg]
        table.cursor_type = "none"
        table.zebra_stripes = True
        yield table

    def on_mount(self) -> None:
        """Set up table columns and fetch logs."""
        table: DataTable = self.query_one("#audit-log-table", DataTable)  # type: ignore[type-arg]
        table.add_column(Text("Timestamp", justify="center"), key="timestamp")
        table.add_column(Text("ID", justify="center"), key="id", width=5)
        table.add_column(
            Text("Name", justify="center"), key="name", width=MAX_RESOURCE_NAME_LENGTH
        )
        table.add_column(Text("Operation", justify="center"), key="operation")
        table.add_column(Text("Changes", justify="center"), key="changes", width=40)
        table.add_column(Text("Client", justify="center"), key="client")
        table.add_column(Text("St", justify="center"), key="status", width=4)

        self.app.run_worker(self._fetch_logs())

    async def _fetch_logs(self) -> None:
        """Fetch audit logs from the last 7 days."""
        from datetime import datetime, timedelta

        try:
            since = datetime.now() - timedelta(days=7)
            result = self._api_client.list_audit_logs(start_date=since, limit=10000)
            self._populate_table(result.logs)
        except Exception as e:
            self.app.notify(f"Failed to load audit logs: {e}", severity="error")
            self.app.pop_screen()

    def _populate_table(self, logs: list[AuditLogOutput]) -> None:
        """Populate the DataTable with audit log entries.

        Args:
            logs: List of audit log entries (newest first from API)
        """
        table: DataTable = self.query_one("#audit-log-table", DataTable)  # type: ignore[type-arg]

        for log in logs:
            style = "red" if not log.success else ""

            ts = Text(log.timestamp.strftime("%m-%d %H:%M:%S"), style=style)
            id_text = Text(str(log.resource_id) if log.resource_id else "", style=style)

            # Resource name (truncated)
            if log.resource_name:
                name = (
                    log.resource_name[:MAX_RESOURCE_NAME_LENGTH] + "\u2026"
                    if len(log.resource_name) > MAX_RESOURCE_NAME_LENGTH
                    else log.resource_name
                )
                name_text = Text(name, style=style)
            else:
                name_text = Text("", style=style)

            op_text = Text(log.operation, style=style)

            # Changes or error
            if not log.success and log.error_message:
                error_msg = (
                    log.error_message[:40] + "..."
                    if len(log.error_message) > 40
                    else log.error_message
                )
                changes_text = Text(error_msg, style="red")
            else:
                changes_str = format_audit_changes(log.old_values, log.new_values)
                changes_text = Text(changes_str, style=style)

            client_text = Text(log.client_name or "", style=style)

            status_text = (
                Text("OK", style="green") if log.success else Text("ER", style="red")
            )

            table.add_row(
                ts, id_text, name_text, op_text, changes_text, client_text, status_text
            )

    def _get_table(self) -> DataTable:  # type: ignore[type-arg]
        """Get the audit log DataTable."""
        return self.query_one("#audit-log-table", DataTable)  # type: ignore[type-arg]

    def action_vi_down(self) -> None:
        """Scroll down one line (j key)."""
        self._get_table().scroll_relative(y=1, animate=False)

    def action_vi_up(self) -> None:
        """Scroll up one line (k key)."""
        self._get_table().scroll_relative(y=-1, animate=False)

    def action_vi_page_down(self) -> None:
        """Scroll down half page (Ctrl+D)."""
        table = self._get_table()
        table.scroll_relative(y=table.size.height // 2, animate=False)

    def action_vi_page_up(self) -> None:
        """Scroll up half page (Ctrl+U)."""
        table = self._get_table()
        table.scroll_relative(y=-(table.size.height // 2), animate=False)

    def action_vi_home(self) -> None:
        """Scroll to top (g key)."""
        self._get_table().scroll_home(animate=False)

    def action_vi_end(self) -> None:
        """Scroll to bottom (G key)."""
        self._get_table().scroll_end(animate=False)

    def action_pop_screen(self) -> None:
        """Go back to the main screen."""
        self.app.pop_screen()
