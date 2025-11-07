"""Table command - Display tasks in flat table format."""

import click

from taskdog.cli.commands.common_options import (
    date_range_options,
    filter_options,
    sort_options,
)
from taskdog.cli.commands.filter_helpers import build_task_filter
from taskdog.cli.commands.table_helpers import render_table
from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog.shared.click_types.field_list import FieldList


@click.command(
    name="table",
    help="Display tasks in flat table format (shows non-archived tasks by default).",
)
@click.option(
    "--fields",
    "-f",
    type=FieldList(),  # No validation - renderer handles unknown fields gracefully
    help="Comma-separated list of fields to display (e.g., 'id,name,note,priority,status'). "
    "Available: id, name, note, priority, status, depends_on, planned_start, planned_end, "
    "actual_start, actual_end, deadline, duration, created_at, tags",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    type=str,
    help="Filter by tags (can be specified multiple times, uses OR logic)",
)
@date_range_options()
@sort_options(default_sort="id")
@filter_options()
@click.pass_context
@handle_command_errors("displaying tasks")
def table_command(ctx, all, status, sort, reverse, fields, tag, start_date, end_date):
    """Display tasks as a flat table.

    By default, shows non-archived tasks (all statuses except archived).
    Use -a/--all to show all tasks including archived.
    Use --status to filter by specific status.
    Use --tag to filter by tags (OR logic when multiple tags specified).
    Use --start-date and --end-date to filter by date range.

    Examples:
        taskdog table                              # Show non-archived tasks
        taskdog table -a                           # Show all tasks (including archived)
        taskdog table --status archived            # Show only archived tasks
        taskdog table --status completed           # Show only completed tasks
        taskdog table -t work -t urgent            # Tasks with tag "work" OR "urgent"
        taskdog table -s priority -r               # Sort by priority descending
        taskdog table --fields id,name,status      # Show specific fields only
        taskdog table --start-date 2025-10-01      # Tasks with dates >= Oct 1
        taskdog table --start-date 2025-10-01 --end-date 2025-10-31  # October tasks
    """
    ctx_obj: CliContext = ctx.obj

    # fields is already parsed by FieldList Click type (no validation)
    # Build integrated filter with all options (tags use OR logic by default)
    tags = list(tag) if tag else None
    filter_obj = build_task_filter(
        all=all,
        status=status,
        tags=tags,
        match_all=False,  # OR logic for multiple tags
        start_date=start_date,
        end_date=end_date,
    )

    # Get filtered and sorted tasks via API client
    result = ctx_obj.api_client.list_tasks(
        filter_obj=filter_obj, sort_by=sort, reverse=reverse
    )

    # Render and display
    render_table(ctx_obj, result, fields=fields)
