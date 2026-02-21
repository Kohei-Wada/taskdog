"""Shared utility for building audit log entry widgets.

Extracted from AuditLogWidget to be reusable across TUI components
(e.g., AuditLogWidget sidebar panel, TaskDetailDialog audit tab).
"""

from typing import Any

from rich.text import Text
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Static

from taskdog_core.application.dto.audit_log_dto import AuditLogOutput


def create_audit_entry_widget(log: AuditLogOutput) -> Vertical:
    """Create a container widget for a log entry.

    Args:
        log: Audit log entry to display

    Returns:
        Vertical container with styled child widgets
    """
    children: list[Static | Horizontal] = []

    # Line 1: Timestamp and status
    ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    status_text = "OK" if log.success else "ER"
    status_class = "log-status-ok" if log.success else "log-status-error"
    header = Horizontal(
        Static(ts, classes="log-timestamp"),
        Static(status_text, classes=status_class),
        classes="log-header",
    )
    children.append(header)

    # Line 2: Operation
    children.append(Static(log.operation, classes="log-operation"))

    # Line 3: Resource info (if exists)
    if log.resource_id or log.resource_name:
        parts: list[str] = []
        if log.resource_id:
            parts.append(f"#{log.resource_id}")
        if log.resource_name:
            name = (
                log.resource_name[:30] + "..."
                if len(log.resource_name) > 30
                else log.resource_name
            )
            parts.append(name)
        children.append(Static(" ".join(parts), classes="log-resource"))

    # Line 4: Changes (if exists)
    changes = format_audit_changes(log.old_values, log.new_values)
    if changes:
        children.append(Static(changes, classes="log-changes"))

    # Line 5: Error message (if failed)
    if not log.success and log.error_message:
        error_msg = (
            log.error_message[:40] + "..."
            if len(log.error_message) > 40
            else log.error_message
        )
        children.append(Static(error_msg, classes="log-error-message"))

    # Line 6: Client (if exists)
    if log.client_name:
        children.append(Static(f"@{log.client_name}", classes="log-client"))

    return Vertical(*children, classes="audit-log-entry")


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

        # Build changes/error text
        if not log.success and log.error_message:
            error_msg = (
                log.error_message[:40] + "..."
                if len(log.error_message) > 40
                else log.error_message
            )
            changes_text = Text(error_msg, style="red")
        else:
            changes_str = format_audit_changes(log.old_values, log.new_values)
            changes_text = Text(changes_str)

        client = log.client_name or ""

        status_text = (
            Text("OK", style="green") if log.success else Text("ER", style="red")
        )

        table.add_row(
            Text(ts),
            Text(log.operation),
            changes_text,
            Text(client),
            status_text,
        )

    return table
