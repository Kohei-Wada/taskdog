"""Table command - Display tasks in flat table format."""

import click

from application.queries.filters.incomplete_filter import IncompleteFilter
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
    help="Show all tasks including completed, failed, and archived",
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
def table_command(ctx, all, sort, reverse, fields):
    """Display tasks as a flat table.

    By default, only shows incomplete tasks (PENDING, IN_PROGRESS).
    Use -a/--all to show all tasks including archived.

    Examples:
        taskdog table                              # Show incomplete tasks
        taskdog table -a                           # Show all tasks (including archived)
        taskdog table -s priority -r               # Sort by priority descending
        taskdog table --fields id,name,status      # Show specific fields only
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    task_query_service = TaskQueryService(repository)

    # Parse fields option
    field_list = None
    if fields:
        # Split by comma and strip whitespace
        field_list = [f.strip() for f in fields.split(",")]

    # Apply filter based on --all flag
    # Show all tasks (no filter) if --all, otherwise show incomplete only
    filter_obj = None if all else IncompleteFilter()

    # Get filtered and sorted tasks
    tasks = task_query_service.get_filtered_tasks(filter_obj, sort_by=sort, reverse=reverse)

    # Render and display
    console_writer = ctx_obj.console_writer
    notes_repository = ctx_obj.notes_repository
    renderer = RichTableRenderer(console_writer, notes_repository)
    renderer.render(tasks, fields=field_list)
