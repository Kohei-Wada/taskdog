"""Table command - Display tasks in flat table format."""

import click

from application.queries.task_query_service import TaskQueryService
from presentation.cli.error_handler import handle_command_errors
from presentation.formatters.rich_table_formatter import RichTableFormatter


@click.command(
    name="table", help="Display tasks in flat table format (shows incomplete tasks by default)."
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Show all tasks including completed and archived ones",
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
@click.pass_context
@handle_command_errors("displaying tasks")
def table_command(ctx, all, sort, reverse):
    """Display tasks as a flat table.

    By default, only shows incomplete tasks (PENDING, IN_PROGRESS, FAILED).
    Use --all to include completed tasks.
    """
    repository = ctx.obj["repository"]
    task_query_service = TaskQueryService(repository)

    # Get tasks using query service
    if all:
        tasks = task_query_service.get_all_tasks(sort_by=sort, reverse=reverse)
    else:
        tasks = task_query_service.get_incomplete_tasks(sort_by=sort, reverse=reverse)

    # Format and display
    formatter = RichTableFormatter()
    output = formatter.format_tasks(tasks, repository)
    print(output)
