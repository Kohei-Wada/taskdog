"""Week command - Display tasks for this week."""

import click

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.this_week_filter import ThisWeekFilter
from presentation.cli.commands.common_options import filter_options, sort_options
from presentation.cli.commands.filter_helpers import build_task_filter
from presentation.cli.commands.table_helpers import get_and_filter_tasks, render_table
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors


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
    repository = ctx_obj.repository

    # Build filter: ThisWeekFilter + status/all filter (AND logic)
    week_filter = ThisWeekFilter()
    status_filter = build_task_filter(all=all, status=status)

    # Combine ThisWeekFilter with status filter
    filter_obj = CompositeFilter([status_filter, week_filter]) if status_filter else week_filter

    # Get filtered and sorted tasks
    week_tasks = get_and_filter_tasks(repository, filter_obj, sort_by=sort, reverse=reverse)

    # Render using shared table renderer
    render_table(ctx_obj, week_tasks)
