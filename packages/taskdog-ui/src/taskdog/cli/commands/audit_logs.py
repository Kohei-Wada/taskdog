"""Audit logs command - Display operation history."""

from datetime import datetime

import click
from rich.table import Table

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog_core.application.dto.audit_log_dto import AuditLogOutput


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


def _format_resource(log: AuditLogOutput) -> str:
    """Format resource display for audit log entry."""
    if log.resource_id and log.resource_name:
        return f"[cyan]#{log.resource_id}[/cyan] {log.resource_name[:18]}"
    if log.resource_id:
        return f"[cyan]#{log.resource_id}[/cyan]"
    if log.resource_name:
        return log.resource_name[:25]
    return "[dim]-[/dim]"


@click.command(
    name="audit-logs",
    help="""Display operation history (audit logs).

Shows a history of operations performed via the API, including task creates,
updates, status changes, and other modifications.

Use filters to narrow down the logs by client name, operation type, task ID, etc.

Examples:
  taskdog audit-logs                           # Show latest 100 logs
  taskdog audit-logs --client claude-code      # Filter by client
  taskdog audit-logs --task 123                # Filter by task ID
  taskdog audit-logs --operation complete_task # Filter by operation
  taskdog audit-logs --since 2025-12-01        # Filter by date
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
def audit_logs_command(
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

    if not result.logs:
        console_writer.info("No audit logs found matching the criteria.")
        return

    # Create Rich table
    table = Table(
        title=f"Audit Logs ({len(result.logs)} of {result.total_count})",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim", width=6)
    table.add_column("Timestamp", width=19)
    table.add_column("Client", width=15)
    table.add_column("Operation", width=18)
    table.add_column("Resource", width=25)
    table.add_column("Status", width=8)

    for log in result.logs:
        table.add_row(
            str(log.id),
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            log.client_name or "[dim]anonymous[/dim]",
            log.operation,
            _format_resource(log),
            "[green]OK[/green]" if log.success else "[red]FAILED[/red]",
        )

    console_writer.print(table)

    # Show pagination info if there are more logs
    if result.total_count > len(result.logs):
        console_writer.info(
            f"Showing {len(result.logs)} of {result.total_count} logs. "
            f"Use --limit to see more."
        )
