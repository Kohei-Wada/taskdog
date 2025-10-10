"""Table command - Display tasks in flat table format."""

import click
from application.queries.task_query_service import TaskQueryService
from presentation.formatters.rich_table_formatter import RichTableFormatter
from presentation.cli.error_handler import handle_command_errors


@click.command(name="table", help="Display tasks in flat table format.")
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Show all tasks including completed ones",
)
@click.pass_context
@handle_command_errors("displaying tasks")
def table_command(ctx, all):
    """Display tasks as a flat table.

    By default, only shows incomplete tasks (PENDING, IN_PROGRESS, FAILED).
    Use --all to include completed tasks.
    """
    repository = ctx.obj["repository"]
    task_query_service = TaskQueryService(repository)

    # Get tasks using query service
    if all:
        tasks = task_query_service.get_all_tasks()
    else:
        tasks = task_query_service.get_incomplete_tasks()

    # Format and display
    formatter = RichTableFormatter()
    output = formatter.format_tasks(tasks, repository)
    print(output)
