"""Audit log screen for TUI - full-page audit log display."""

from typing import ClassVar

from taskdog_client import TaskdogApiClient
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Header

from taskdog.tui.widgets.audit_log_table import AuditLogTable


class AuditLogScreen(ModalScreen[None]):
    """Full-page screen for displaying audit log entries.

    Uses ModalScreen to block App-level bindings (add, start, done, etc.)
    so only audit-specific keys are active.

    Shows all audit log columns in a full-width DataTable:
    Timestamp, ID, Name, Operation, Changes, Client, Status.
    """

    BINDINGS: ClassVar = [
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
        table = AuditLogTable(id="audit-log-table")
        table.border_title = "Audit Log"
        yield table

    def on_mount(self) -> None:
        """Fetch logs after screen is mounted."""
        table = self.query_one("#audit-log-table", AuditLogTable)
        table.focus()
        self.app.run_worker(self._fetch_logs())

    async def _fetch_logs(self) -> None:
        """Fetch audit logs from the last 7 days."""
        from datetime import datetime, timedelta

        try:
            since = datetime.now() - timedelta(days=7)
            result = self._api_client.list_audit_logs(start_date=since, limit=10000)
            table = self.query_one("#audit-log-table", AuditLogTable)
            table.load_logs(result.logs)
        except Exception as e:
            self.app.notify(f"Failed to load audit logs: {e}", severity="error")
            self.app.pop_screen()

    def action_pop_screen(self) -> None:
        """Go back to the main screen."""
        self.app.pop_screen()
