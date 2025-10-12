"""Tree command - Display tasks in hierarchical tree format."""

import click

from application.queries.task_query_service import TaskQueryService
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.formatters.rich_tree_formatter import RichTreeFormatter


@click.command(
    name="tree",
    help="Display tasks in hierarchical tree format (shows incomplete tasks by default).",
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
def tree_command(ctx, all, sort, reverse):
    """Display tasks as a hierarchical tree.

    By default, only shows incomplete tasks (PENDING, IN_PROGRESS, FAILED).
    Completed parent tasks are shown if they have incomplete children.
    Use --all to include all completed tasks.
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    task_query_service = TaskQueryService(repository)

    # Get tasks using query service
    if all:
        tasks = task_query_service.get_all_tasks(sort_by=sort, reverse=reverse)
    else:
        tasks = task_query_service.get_incomplete_tasks_with_hierarchy(
            sort_by=sort, reverse=reverse
        )

    # Format and display
    formatter = RichTreeFormatter()
    output = formatter.format_tasks(tasks, repository)
    print(output)
