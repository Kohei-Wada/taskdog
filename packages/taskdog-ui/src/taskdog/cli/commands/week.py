"""Week command - Display tasks for this week."""

from datetime import date, timedelta

import click

from taskdog.cli.commands.common_options import filter_options, sort_options
from taskdog.cli.commands.table_helpers import render_table
from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors


@click.command(
    name="week",
    help="Display tasks for this week (shows incomplete tasks by default).",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["table"]),
    default="table",
    help="Display format (default: table)",
)
@sort_options(default_sort="deadline")
@filter_options()
@click.pass_context
@handle_command_errors("displaying tasks")
def week_command(ctx, format, all, status, sort, reverse):
    """Display tasks for this week.

    Shows tasks that meet any of these criteria:
    - Deadline is within this week (Monday to Sunday)
    - Planned period overlaps with this week
    - Status is IN_PROGRESS

    By default, shows incomplete tasks (PENDING, IN_PROGRESS) only.
    Use -a/--all to include all tasks (including archived).
    Use --status to filter by specific status.

    Examples:
        taskdog week                    # Show incomplete tasks for this week
        taskdog week -a                 # Show all tasks (including completed)
        taskdog week --status pending   # Show only pending tasks for this week
        taskdog week --sort priority    # Sort by priority
    """
    ctx_obj: CliContext = ctx.obj

    # Get this week's date range for filtering (Monday to Sunday)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Get filtered and sorted tasks via API client
    result = ctx_obj.api_client.list_tasks(
        all=all,
        status=status,
        start_date=week_start,
        end_date=week_end,
        sort_by=sort,
        reverse=reverse,
    )

    # Render and display
    render_table(ctx_obj, result)
