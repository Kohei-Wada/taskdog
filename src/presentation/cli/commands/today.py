"""Today command - Display tasks for today."""

import click
from presentation.formatters.rich_tree_formatter import RichTreeFormatter
from presentation.formatters.rich_table_formatter import RichTableFormatter


@click.command(name="today", help="Display tasks for today.")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["tree", "table"]),
    default="tree",
    help="Display format (default: tree)",
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Show all tasks including completed ones",
)
@click.pass_context
def today_command_new(ctx, format, all):
    """Display tasks for today.

    Shows tasks that meet any of these criteria:
    - Deadline is today
    - Planned period includes today (planned_start <= today <= planned_end)
    - Status is IN_PROGRESS

    By default, completed tasks are excluded unless --all is specified.
    Parent tasks are included if they have children matching today's criteria.
    """
    query_service = ctx.obj["task_query_service"]
    repository = ctx.obj["repository"]

    try:
        # Get today's tasks (filtered and sorted)
        today_tasks = query_service.get_today_tasks(include_completed=all)

        # Format and display
        if format == "tree":
            formatter = RichTreeFormatter()
        else:
            formatter = RichTableFormatter()

        output = formatter.format_tasks(today_tasks, repository)
        print(output)
    except Exception as e:
        print(f"Error displaying tasks: {e}")
