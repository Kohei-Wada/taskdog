"""Today command - Display tasks for today."""

import click

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.today_filter import TodayFilter
from application.queries.task_query_service import TaskQueryService
from presentation.cli.commands.filter_helpers import build_task_filter
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.renderers.rich_table_renderer import RichTableRenderer


@click.command(
    name="today",
    help="Display tasks for today (shows incomplete tasks by default).",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["table"]),
    default="table",
    help="Display format (default: table)",
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Show all tasks including completed, failed, and archived",
)
@click.option(
    "--status",
    type=click.Choice(
        ["pending", "in_progress", "completed", "canceled", "archived"], case_sensitive=False
    ),
    default=None,
    help="Filter tasks by status (overrides --all)",
)
@click.option(
    "--sort",
    "-s",
    type=click.Choice(["id", "priority", "deadline", "name", "status", "planned_start"]),
    default="deadline",
    help="Sort tasks by specified field (default: deadline)",
)
@click.option(
    "--reverse",
    "-r",
    is_flag=True,
    help="Reverse sort order",
)
@click.pass_context
@handle_command_errors("displaying tasks")
def today_command(ctx, format, all, status, sort, reverse):
    """Display tasks for today.

    Shows tasks that meet any of these criteria:
    - Deadline is today
    - Planned period includes today (planned_start <= today <= planned_end)
    - Status is IN_PROGRESS

    By default, shows incomplete tasks (PENDING, IN_PROGRESS) only.
    Use -a/--all to include all tasks (including archived).
    Use --status to filter by specific status.
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    query_service = TaskQueryService(repository)

    # Build filter: TodayFilter + status/all filter (AND logic)
    today_filter = TodayFilter()
    status_filter = build_task_filter(all=all, status=status)

    # Combine TodayFilter with status filter
    filter_obj = CompositeFilter([status_filter, today_filter]) if status_filter else today_filter

    today_tasks = query_service.get_filtered_tasks(filter_obj, sort_by=sort, reverse=reverse)

    renderer = RichTableRenderer(ctx_obj.console_writer, ctx_obj.notes_repository)
    renderer.render(today_tasks)
