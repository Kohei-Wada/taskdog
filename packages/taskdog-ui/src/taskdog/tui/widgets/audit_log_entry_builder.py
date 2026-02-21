"""Shared utility for building audit log display data.

Reusable across TUI components
(e.g., AuditLogTable, TaskDetailDialog audit tab).
"""

from typing import Any

from rich.text import Text
from textual.widgets import DataTable

from taskdog_core.application.dto.audit_log_dto import AuditLogOutput

MAX_CHANGES_LENGTH = 40
MAX_ERROR_LENGTH = 40


def format_audit_changes(
    old_values: dict[str, Any] | None,
    new_values: dict[str, Any] | None,
) -> str:
    """Format changes between old and new values.

    Args:
        old_values: Values before the change
        new_values: Values after the change

    Returns:
        Formatted change string (e.g., "priority: 3 -> 5")
    """
    if not old_values and not new_values:
        return ""

    changes: list[str] = []

    all_keys: set[str] = set()
    if old_values:
        all_keys.update(old_values.keys())
    if new_values:
        all_keys.update(new_values.keys())

    for key in sorted(all_keys):
        old_val = old_values.get(key) if old_values else None
        new_val = new_values.get(key) if new_values else None

        if old_val != new_val:
            old_str = format_audit_value(old_val)
            new_str = format_audit_value(new_val)
            changes.append(f"{key}: {old_str} \u2192 {new_str}")

    # Limit to 2 changes to keep it compact
    if len(changes) > 2:
        return ", ".join(changes[:2]) + f" (+{len(changes) - 2})"
    return ", ".join(changes)


def format_audit_value(value: Any) -> str:
    """Format a single value for display.

    Args:
        value: Value to format

    Returns:
        Formatted string representation
    """
    if value is None:
        return "\u2205"
    if isinstance(value, bool):
        return "\u2713" if value else "\u2717"
    if isinstance(value, str) and len(value) > 15:
        return value[:15] + "..."
    return str(value)


def build_changes_text(log: AuditLogOutput, style: str = "") -> Text:
    """Build the changes/error column text for an audit log entry.

    Args:
        log: Audit log entry
        style: Base style to apply (e.g., "red" for failed entries)

    Returns:
        Formatted Rich Text for changes column
    """
    if not log.success and log.error_message:
        error_msg = (
            log.error_message[:MAX_ERROR_LENGTH] + "..."
            if len(log.error_message) > MAX_ERROR_LENGTH
            else log.error_message
        )
        return Text(error_msg, style="red")

    changes_str = format_audit_changes(log.old_values, log.new_values)
    return Text(changes_str, style=style)


def build_status_text(log: AuditLogOutput) -> Text:
    """Build the status column text for an audit log entry.

    Args:
        log: Audit log entry

    Returns:
        "OK" in green or "ER" in red
    """
    return Text("OK", style="green") if log.success else Text("ER", style="red")


def create_audit_log_table(logs: list[AuditLogOutput]) -> DataTable:  # type: ignore[type-arg]
    """Create a DataTable widget for displaying audit log entries.

    Used by TaskDetailDialog for compact, tabular audit log display.
    Resource info (ID, name) is omitted since the dialog already shows it.

    Args:
        logs: List of audit log entries to display

    Returns:
        DataTable widget with audit log data
    """
    table: DataTable = DataTable(  # type: ignore[type-arg]
        id="audit-log-table",
    )
    table.cursor_type = "none"
    table.zebra_stripes = True
    table.can_focus = False

    table.add_column(Text("Timestamp", justify="center"), key="timestamp")
    table.add_column(Text("Operation", justify="center"), key="operation")
    table.add_column(Text("Changes", justify="center"), key="changes", width=40)
    table.add_column(Text("Client", justify="center"), key="client")
    table.add_column(Text("St", justify="center"), key="status")

    for log in logs:
        ts = log.timestamp.strftime("%m-%d %H:%M:%S")

        table.add_row(
            Text(ts),
            Text(log.operation),
            build_changes_text(log),
            Text(log.client_name or ""),
            build_status_text(log),
        )

    return table
