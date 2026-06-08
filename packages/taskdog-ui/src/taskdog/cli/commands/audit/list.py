"""`audit list` - Display operation history."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import click
from rich.table import Table

from taskdog.cli.error_handler import handle_command_errors
from taskdog.constants.audit_log import (
    AUDIT_CHANGES_WIDTH,
    AUDIT_CLIENT_WIDTH,
    AUDIT_ID_WIDTH,
    AUDIT_OPERATION_WIDTH,
    AUDIT_STATUS_WIDTH,
    AUDIT_TIMESTAMP_WIDTH,
    COLUMN_AUDIT_ID_STYLE,
    COLUMN_AUDIT_STATUS_FAIL_STYLE,
    COLUMN_AUDIT_STATUS_OK_STYLE,
    HEADER_AUDIT_CHANGES,
    HEADER_AUDIT_CLIENT,
    HEADER_AUDIT_OPERATION,
    HEADER_AUDIT_STATUS,
    HEADER_AUDIT_TIMESTAMP,
    JUSTIFY_AUDIT_CHANGES,
)
from taskdog.constants.common import HEADER_ID, HEADER_NAME, TABLE_HEADER_STYLE
from taskdog.constants.formatting import format_table_title
from taskdog.formatters.audit_log_formatter import compact_changes, truncate_error
from taskdog.presenters.audit_log_presenter import AuditLogPresenter

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext
    from taskdog.view_models.audit_log_view_model import AuditLogRowViewModel


def _parse_date_filter(date_str: str, end_of_day: bool = False) -> datetime:
    """Parse a date filter string to datetime.

    Args:
        date_str: ISO format date or datetime string
        end_of_day: If True and only date provided, use end of day

    Returns:
        Parsed datetime object
    """
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        suffix = "T23:59:59" if end_of_day else "T00:00:00"
        return datetime.fromisoformat(f"{date_str}{suffix}")


def _format_resource(row: AuditLogRowViewModel) -> str:
    """Format resource display for audit log entry."""
    if row.resource_id and row.resource_name:
        return f"[cyan]#{row.resource_id}[/cyan] {row.resource_name}"
    if row.resource_id:
        return f"[cyan]#{row.resource_id}[/cyan]"
    if row.resource_name:
        return row.resource_name
    return "[dim]-[/dim]"


def _format_changes(row: AuditLogRowViewModel) -> str:
    """Format changes display for audit log entry."""
    if not row.success and row.error_message:
        error_msg = truncate_error(row.error_message, AUDIT_CHANGES_WIDTH)
        return f"[red]{error_msg}[/red]"
    return compact_changes(row.changes, AUDIT_CHANGES_WIDTH)


@click.command(
    name="list",
    help="""Display operation history (audit logs).

Shows a history of operations performed via the API, including task creates,
updates, status changes, and other modifications.

Use filters to narrow down the logs by client name, operation type, task ID, etc.

Examples:
  taskdog audit list                           # Show latest 100 logs
  taskdog audit list --client claude-code      # Filter by client
  taskdog audit list --task 123                # Filter by task ID
  taskdog audit list --operation complete_task # Filter by operation
  taskdog audit list --since 2025-12-01        # Filter by date
""",
)
@click.option(
    "--client",
    "-c",
    "client_filter",
    type=str,
    default=None,
    help="Filter by client name (e.g., 'claude-code')",
)
@click.option(
    "--operation",
    "-o",
    type=str,
    default=None,
    help="Filter by operation type (e.g., 'create_task', 'complete_task')",
)
@click.option(
    "--task",
    "-t",
    "task_id",
    type=int,
    default=None,
    help="Filter by task ID",
)
@click.option(
    "--since",
    type=str,
    default=None,
    help="Show logs since this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--until",
    type=str,
    default=None,
    help="Show logs until this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--limit",
    "-n",
    type=click.IntRange(1, 1000),
    default=100,
    help="Maximum number of logs to show (default: 100, max: 1000)",
)
@click.option(
    "--failed",
    is_flag=True,
    default=False,
    help="Show only failed operations",
)
@click.pass_context
@handle_command_errors("fetching audit logs")
def list_command(
    ctx: click.Context,
    client_filter: str | None,
    operation: str | None,
    task_id: int | None,
    since: str | None,
    until: str | None,
    limit: int,
    failed: bool,
) -> None:
    """Display operation history (audit logs)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    api_client = ctx_obj.api_client

    # Parse date filters
    start_date = _parse_date_filter(since) if since else None
    end_date = _parse_date_filter(until, end_of_day=True) if until else None

    # Fetch audit logs via API
    result = api_client.list_audit_logs(
        client_filter=client_filter,
        operation=operation,
        resource_type="task" if task_id else None,
        resource_id=task_id,
        success=False if failed else None,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    view_model = AuditLogPresenter().present(result)

    if not view_model.rows:
        console_writer.info("No audit logs found matching the criteria.")
        return

    # Create Rich table
    table = Table(
        title=format_table_title(
            f"Audit Logs ({len(view_model.rows)} of {view_model.total_count})"
        ),
        show_header=True,
        header_style=TABLE_HEADER_STYLE,
    )
    table.add_column(HEADER_AUDIT_TIMESTAMP, width=AUDIT_TIMESTAMP_WIDTH)
    table.add_column(HEADER_ID, style=COLUMN_AUDIT_ID_STYLE, width=AUDIT_ID_WIDTH)
    table.add_column(HEADER_NAME)
    table.add_column(HEADER_AUDIT_OPERATION, width=AUDIT_OPERATION_WIDTH)
    table.add_column(
        HEADER_AUDIT_CHANGES,
        width=AUDIT_CHANGES_WIDTH,
        justify=JUSTIFY_AUDIT_CHANGES,
    )
    table.add_column(HEADER_AUDIT_CLIENT, width=AUDIT_CLIENT_WIDTH)
    table.add_column(HEADER_AUDIT_STATUS, width=AUDIT_STATUS_WIDTH)

    for row in view_model.rows:
        status_style = (
            COLUMN_AUDIT_STATUS_OK_STYLE
            if row.success
            else COLUMN_AUDIT_STATUS_FAIL_STYLE
        )
        status_label = "OK" if row.success else "FAILED"
        table.add_row(
            row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            str(row.id),
            _format_resource(row),
            row.operation,
            _format_changes(row),
            row.client_name or "[dim]anonymous[/dim]",
            f"[{status_style}]{status_label}[/{status_style}]",
        )

    console_writer.print(table)

    # Show pagination info if there are more logs
    if view_model.total_count > len(view_model.rows):
        console_writer.info(
            f"Showing {len(view_model.rows)} of {view_model.total_count} logs. "
            f"Use --limit to see more."
        )
