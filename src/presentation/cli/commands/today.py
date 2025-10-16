"""Today command - Display tasks for today."""

import click

from application.queries.task_query_service import TaskQueryService
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.renderers.rich_table_renderer import RichTableRenderer


@click.command(name="today", help="Display tasks for today (deadline, planned, or in-progress).")
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
    help="Show all tasks including completed ones",
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
def today_command(ctx, format, all, sort, reverse):
    """Display tasks for today.

    Shows tasks that meet any of these criteria:
    - Deadline is today
    - Planned period includes today (planned_start <= today <= planned_end)
    - Status is IN_PROGRESS

    By default, completed tasks are excluded unless --all is specified.
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    query_service = TaskQueryService(repository)

    # Get today's tasks (filtered and sorted)
    today_tasks = query_service.get_today_tasks(
        include_completed=all, sort_by=sort, reverse=reverse
    )

    # Render and display
    console_writer = ctx_obj.console_writer
    renderer = RichTableRenderer(console_writer)
    renderer.render(today_tasks, repository)
