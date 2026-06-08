"""Audit log table widget for TUI.

A DataTable widget for displaying audit log entries with Vi-style navigation.
Used by AuditLogScreen for full-page audit log display.
"""

from typing import Any, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.widgets import DataTable

from taskdog.constants.audit_log import (
    AUDIT_TUI_CHANGES_WIDTH,
    AUDIT_TUI_ID_WIDTH,
    AUDIT_TUI_NAME_WIDTH,
    AUDIT_TUI_STATUS_WIDTH,
    HEADER_AUDIT_CHANGES,
    HEADER_AUDIT_CLIENT,
    HEADER_AUDIT_OPERATION,
    HEADER_AUDIT_STATUS,
    HEADER_AUDIT_TIMESTAMP,
    JUSTIFY_AUDIT_CHANGES,
    JUSTIFY_AUDIT_CLIENT,
    JUSTIFY_AUDIT_ID,
    JUSTIFY_AUDIT_NAME,
    JUSTIFY_AUDIT_OPERATION,
    JUSTIFY_AUDIT_STATUS,
    JUSTIFY_AUDIT_TIMESTAMP,
)
from taskdog.constants.common import HEADER_ID, HEADER_NAME
from taskdog.constants.task_table import PAGE_SCROLL_SIZE
from taskdog.tui.widgets.audit_log_entry_builder import (
    build_changes_text,
    build_status_text,
)
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog.view_models.audit_log_view_model import AuditLogRowViewModel


class AuditLogTable(DataTable, ViNavigationMixin):  # type: ignore[type-arg]
    """A DataTable widget for displaying audit log entries.

    Features:
    - Full-width columns: Timestamp, ID, Name, Operation, Changes, Client, Status
    - Vi-style keyboard navigation aligned with TaskTable (j/k/g/G/Ctrl+d/Ctrl+u)
    - Row cursor for navigation
    - Error rows highlighted in red
    """

    BINDINGS: ClassVar = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "vi_home", "Top", show=False),
        Binding("G", "vi_end", "Bottom", show=False),
        *ViNavigationMixin.VI_PAGE_BINDINGS,
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the audit log table."""
        super().__init__(**kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True

    def _safe_move_cursor(self, row: int) -> None:
        if self.row_count > 0:
            self.move_cursor(row=row)

    def action_vi_home(self) -> None:
        self._safe_move_cursor(row=0)

    def action_vi_end(self) -> None:
        if self.row_count > 0:
            self._safe_move_cursor(row=self.row_count - 1)

    def action_vi_page_down(self) -> None:
        if self.row_count > 0:
            new_row = min(self.cursor_row + PAGE_SCROLL_SIZE, self.row_count - 1)
            self._safe_move_cursor(row=new_row)

    def action_vi_page_up(self) -> None:
        if self.row_count > 0:
            new_row = max(self.cursor_row - PAGE_SCROLL_SIZE, 0)
            self._safe_move_cursor(row=new_row)

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
            Text(HEADER_AUDIT_STATUS, justify=JUSTIFY_AUDIT_STATUS),
            key="status",
            width=AUDIT_TUI_STATUS_WIDTH,
        )

    def load_logs(self, rows: tuple[AuditLogRowViewModel, ...]) -> None:
        """Load audit log entries into the table.

        Args:
            rows: Audit log row view models (newest first from API)
        """
        with self.app.batch_update():
            self.clear(columns=False)

            for row in rows:
                style = "red" if not row.success else ""

                ts = Text(row.timestamp.strftime("%m-%d %H:%M:%S"), style=style)
                id_text = Text(
                    str(row.resource_id) if row.resource_id else "", style=style
                )

                if row.resource_name:
                    name = (
                        row.resource_name[:AUDIT_TUI_NAME_WIDTH] + "…"
                        if len(row.resource_name) > AUDIT_TUI_NAME_WIDTH
                        else row.resource_name
                    )
                    name_text = Text(name, style=style)
                else:
                    name_text = Text("", style=style)

                op_text = Text(row.operation, style=style)

                self.add_row(
                    ts,
                    id_text,
                    name_text,
                    op_text,
                    build_changes_text(row, style),
                    Text(row.client_name or "", style=style),
                    build_status_text(row),
                )
