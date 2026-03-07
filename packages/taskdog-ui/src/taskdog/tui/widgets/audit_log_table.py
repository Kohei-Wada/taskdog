"""Audit log table widget for TUI.

A DataTable widget for displaying audit log entries with Vi-style navigation.
Used by AuditLogScreen for full-page audit log display.
"""

from typing import Any, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.widgets import DataTable

from taskdog.constants.column_headers import (
    HEADER_AUDIT_CHANGES,
    HEADER_AUDIT_CLIENT,
    HEADER_AUDIT_OPERATION,
    HEADER_AUDIT_STATUS_SHORT,
    HEADER_AUDIT_TIMESTAMP,
    HEADER_ID,
    HEADER_NAME,
)
from taskdog.constants.table_dimensions import (
    AUDIT_TUI_CHANGES_WIDTH,
    AUDIT_TUI_ID_WIDTH,
    AUDIT_TUI_NAME_WIDTH,
    AUDIT_TUI_STATUS_WIDTH,
)
from taskdog.constants.table_styles import (
    JUSTIFY_AUDIT_CHANGES,
    JUSTIFY_AUDIT_CLIENT,
    JUSTIFY_AUDIT_ID,
    JUSTIFY_AUDIT_NAME,
    JUSTIFY_AUDIT_OPERATION,
    JUSTIFY_AUDIT_STATUS,
    JUSTIFY_AUDIT_TIMESTAMP,
)
from taskdog.tui.widgets.audit_log_entry_builder import (
    build_changes_text,
    build_status_text,
)
from taskdog.tui.widgets.base_widget import TUIWidget
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog_core.application.dto.audit_log_dto import AuditLogOutput


class AuditLogTable(DataTable, TUIWidget, ViNavigationMixin):  # type: ignore[type-arg]
    """A DataTable widget for displaying audit log entries.

    Features:
    - Full-width columns: Timestamp, ID, Name, Operation, Changes, Client, Status
    - Vi-style keyboard navigation (j/k/g/G/Ctrl+d/Ctrl+u)
    - Error rows highlighted in red
    """

    BINDINGS: ClassVar = [
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
        Binding("g", "goto_top", "Top", show=False),
        Binding("G", "goto_bottom", "Bottom", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the audit log table."""
        super().__init__(**kwargs)
        self.cursor_type = "none"
        self.zebra_stripes = True

    def action_scroll_down(self) -> None:
        """Scroll down one line."""
        self.scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        """Scroll up one line."""
        self.scroll_up(animate=False)

    def action_goto_top(self) -> None:
        """Scroll to the top of the table."""
        self.scroll_home(animate=False)

    def action_goto_bottom(self) -> None:
        """Scroll to the bottom of the table."""
        self.scroll_end(animate=False)

    def on_mount(self) -> None:
        """Set up table columns."""
        self.add_column(
            Text(HEADER_AUDIT_TIMESTAMP, justify=JUSTIFY_AUDIT_TIMESTAMP),
            key="timestamp",
        )
        self.add_column(
            Text(HEADER_ID, justify=JUSTIFY_AUDIT_ID),
            key="id",
            width=AUDIT_TUI_ID_WIDTH,
        )
        self.add_column(
            Text(HEADER_NAME, justify=JUSTIFY_AUDIT_NAME),
            key="name",
            width=AUDIT_TUI_NAME_WIDTH,
        )
        self.add_column(
            Text(HEADER_AUDIT_OPERATION, justify=JUSTIFY_AUDIT_OPERATION),
            key="operation",
        )
        self.add_column(
            Text(HEADER_AUDIT_CHANGES, justify=JUSTIFY_AUDIT_CHANGES),
            key="changes",
            width=AUDIT_TUI_CHANGES_WIDTH,
        )
        self.add_column(
            Text(HEADER_AUDIT_CLIENT, justify=JUSTIFY_AUDIT_CLIENT), key="client"
        )
        self.add_column(
            Text(HEADER_AUDIT_STATUS_SHORT, justify=JUSTIFY_AUDIT_STATUS),
            key="status",
            width=AUDIT_TUI_STATUS_WIDTH,
        )

    def load_logs(self, logs: list[AuditLogOutput]) -> None:
        """Load audit log entries into the table.

        Args:
            logs: List of audit log entries (newest first from API)
        """
        with self.app.batch_update():
            self.clear(columns=False)

            for log in logs:
                style = "red" if not log.success else ""

                ts = Text(log.timestamp.strftime("%m-%d %H:%M:%S"), style=style)
                id_text = Text(
                    str(log.resource_id) if log.resource_id else "", style=style
                )

                # Resource name (truncated)
                if log.resource_name:
                    name = (
                        log.resource_name[:AUDIT_TUI_NAME_WIDTH] + "\u2026"
                        if len(log.resource_name) > AUDIT_TUI_NAME_WIDTH
                        else log.resource_name
                    )
                    name_text = Text(name, style=style)
                else:
                    name_text = Text("", style=style)

                op_text = Text(log.operation, style=style)

                self.add_row(
                    ts,
                    id_text,
                    name_text,
                    op_text,
                    build_changes_text(log, style),
                    Text(log.client_name or "", style=style),
                    build_status_text(log),
                )
