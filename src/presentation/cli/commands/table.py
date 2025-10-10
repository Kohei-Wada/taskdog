"""Table command - Display tasks in flat table format."""

import click
from presentation.formatters.rich_table_formatter import RichTableFormatter


@click.command(name="table", help="Display tasks in flat table format.")
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Show all tasks including completed ones",
)
@click.pass_context
def table_command(ctx, all):
    """Display tasks as a flat table.

    By default, only shows incomplete tasks (PENDING, IN_PROGRESS, FAILED).
    Use --all to include completed tasks.
    """
    repository = ctx.obj["repository"]
    task_query_service = ctx.obj["task_query_service"]

    try:
        # Get tasks using query service
        if all:
            tasks = task_query_service.get_all_tasks()
        else:
            tasks = task_query_service.get_incomplete_tasks()

        # Format and display
        formatter = RichTableFormatter()
        output = formatter.format_tasks(tasks, repository)
        print(output)
    except Exception as e:
        print(f"Error displaying tasks: {e}")
