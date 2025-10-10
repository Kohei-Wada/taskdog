"""Tree command - Display tasks in hierarchical tree format."""

import click
from presentation.formatters.rich_tree_formatter import RichTreeFormatter


@click.command(name="tree", help="Display tasks in hierarchical tree format.")
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Show all tasks including completed ones",
)
@click.pass_context
def tree_command(ctx, all):
    """Display tasks as a hierarchical tree.

    By default, only shows incomplete tasks (PENDING, IN_PROGRESS, FAILED).
    Completed parent tasks are shown if they have incomplete children.
    Use --all to include all completed tasks.
    """
    repository = ctx.obj["repository"]
    task_query_service = ctx.obj["task_query_service"]

    try:
        # Get tasks using query service
        if all:
            tasks = task_query_service.get_all_tasks()
        else:
            tasks = task_query_service.get_incomplete_tasks_with_hierarchy()

        # Format and display
        formatter = RichTreeFormatter()
        output = formatter.format_tasks(tasks, repository)
        print(output)
    except Exception as e:
        print(f"Error displaying tasks: {e}")
