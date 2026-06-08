"""Shared utility for building audit log display data.

Reusable across TUI components
(e.g., AuditLogTable, TaskDetailDialog audit tab).
"""

from rich.text import Text
from textual.widgets import DataTable

from taskdog.constants.audit_log import (
    AUDIT_TUI_CHANGES_WIDTH,
    COLUMN_AUDIT_STATUS_FAIL_STYLE,
    COLUMN_AUDIT_STATUS_OK_STYLE,
    HEADER_AUDIT_CHANGES,
    HEADER_AUDIT_CLIENT,
    HEADER_AUDIT_OPERATION,
    HEADER_AUDIT_STATUS,
    HEADER_AUDIT_TIMESTAMP,
    JUSTIFY_AUDIT_CHANGES,
    JUSTIFY_AUDIT_CLIENT,
    JUSTIFY_AUDIT_OPERATION,
    JUSTIFY_AUDIT_STATUS,
    JUSTIFY_AUDIT_TIMESTAMP,
)
from taskdog.formatters.audit_log_formatter import compact_changes, truncate_error
from taskdog.view_models.audit_log_view_model import AuditLogRowViewModel

MAX_CHANGES_LENGTH = AUDIT_TUI_CHANGES_WIDTH
MAX_ERROR_LENGTH = 40


def build_changes_text(row: AuditLogRowViewModel, style: str = "") -> Text:
    """Build the changes/error column text for an audit log entry.

    Args:
        row: Audit log row view model
        style: Base style to apply (e.g., "red" for failed entries)

    Returns:
        Formatted Rich Text for changes column
    """
    if not row.success and row.error_message:
        return Text(truncate_error(row.error_message, MAX_ERROR_LENGTH), style="red")

    return Text(compact_changes(row.changes, MAX_CHANGES_LENGTH), style=style)


def build_status_text(row: AuditLogRowViewModel) -> Text:
    """Build the status column text for an audit log entry.

    Args:
        row: Audit log row view model

    Returns:
        "OK" in green or "ER" in red
    """
    return (
        Text("OK", style=COLUMN_AUDIT_STATUS_OK_STYLE)
        if row.success
        else Text("ER", style=COLUMN_AUDIT_STATUS_FAIL_STYLE)
    )


def create_audit_log_table(
    rows: tuple[AuditLogRowViewModel, ...],
) -> DataTable:  # type: ignore[type-arg]
    """Create a DataTable widget for displaying audit log entries.

    Used by TaskDetailDialog for compact, tabular audit log display.
    Resource info (ID, name) is omitted since the dialog already shows it.

    Args:
        rows: Audit log row view models to display

    Returns:
        DataTable widget with audit log data
    """
    table: DataTable = DataTable(  # type: ignore[type-arg]
        id="audit-log-table",
    )
    table.cursor_type = "none"
    table.zebra_stripes = True
    table.can_focus = False

    table.add_column(
        Text(HEADER_AUDIT_TIMESTAMP, justify=JUSTIFY_AUDIT_TIMESTAMP), key="timestamp"
    )
    table.add_column(
        Text(HEADER_AUDIT_OPERATION, justify=JUSTIFY_AUDIT_OPERATION), key="operation"
    )
    table.add_column(
        Text(HEADER_AUDIT_CHANGES, justify=JUSTIFY_AUDIT_CHANGES),
        key="changes",
        width=AUDIT_TUI_CHANGES_WIDTH,
    )
    table.add_column(
        Text(HEADER_AUDIT_CLIENT, justify=JUSTIFY_AUDIT_CLIENT), key="client"
    )
    table.add_column(
        Text(HEADER_AUDIT_STATUS, justify=JUSTIFY_AUDIT_STATUS), key="status"
    )

    for row in rows:
        ts = row.timestamp.strftime("%m-%d %H:%M:%S")

        table.add_row(
            Text(ts),
            Text(row.operation),
            build_changes_text(row),
            Text(row.client_name or ""),
            build_status_text(row),
        )

    return table
