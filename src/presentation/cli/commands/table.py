"""Table command - Display tasks in flat table format."""

import click

from application.queries.filters.active_filter import ActiveFilter
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.filters.this_week_filter import ThisWeekFilter
from application.queries.filters.today_filter import TodayFilter
from application.queries.task_query_service import TaskQueryService
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.renderers.rich_table_renderer import RichTableRenderer


@click.command(
    name="table", help="Display tasks in flat table format (shows incomplete tasks by default)."
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Show all active tasks including completed and failed (archived tasks are never shown)",
)
@click.option(
    "--filter",
    type=click.Choice(["all", "incomplete", "today", "week"]),
    default=None,
    help="Filter tasks by criteria: all (all tasks), incomplete (default), "
    "today (today's tasks), week (this week's tasks)",
)
@click.option(
    "--sort",
    "-s",
    type=click.Choice(["id", "priority", "deadline", "name", "status", "planned_start"]),
    default="id",
    help="Sort tasks by specified field (default: id)",
)
@click.option(
    "--reverse",
    "-r",
    is_flag=True,
    help="Reverse sort order",
)
@click.option(
    "--fields",
    "-f",
    type=str,
    help="Comma-separated list of fields to display (e.g., 'id,name,note,priority,status'). "
    "Available: id, name, note, priority, status, depends_on, planned_start, planned_end, "
    "actual_start, actual_end, deadline, duration, created_at",
)
@click.pass_context
@handle_command_errors("displaying tasks")
def table_command(ctx, all, filter, sort, reverse, fields):
    """Display tasks as a flat table.

    By default, only shows incomplete tasks (PENDING, IN_PROGRESS).
    Use --filter to apply different filtering criteria.
    Archived tasks are never shown.

    Examples:
        taskdog table                              # Show incomplete tasks
        taskdog table -a                           # Include completed/failed tasks
        taskdog table --filter today               # Show today's tasks
        taskdog table --filter week                # Show this week's tasks
        taskdog table --filter all                 # Show all active tasks (same as -a)
        taskdog table --filter week --fields id,name,deadline  # Combine options
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    task_query_service = TaskQueryService(repository)

    # Parse fields option
    field_list = None
    if fields:
        # Split by comma and strip whitespace
        field_list = [f.strip() for f in fields.split(",")]

    # Determine filter type (--all flag overrides --filter option for backward compatibility)
    if all:
        filter_type = "all"
    elif filter:
        filter_type = filter
    else:
        filter_type = "incomplete"

    # Create appropriate filter object
    if filter_type == "all":
        # Show all active tasks (exclude archived only)
        filter_obj = ActiveFilter()
    elif filter_type == "incomplete":
        filter_obj = IncompleteFilter()
    elif filter_type == "today":
        filter_obj = TodayFilter(include_completed=False)
    elif filter_type == "week":
        filter_obj = ThisWeekFilter(include_completed=False)
    else:
        filter_obj = IncompleteFilter()  # Default fallback

    # Get filtered and sorted tasks
    tasks = task_query_service.get_filtered_tasks(filter_obj, sort_by=sort, reverse=reverse)

    # Render and display
    console_writer = ctx_obj.console_writer
    notes_repository = ctx_obj.notes_repository
    renderer = RichTableRenderer(console_writer, notes_repository)
    renderer.render(tasks, fields=field_list)
