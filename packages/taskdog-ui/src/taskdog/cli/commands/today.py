"""Today command - Display tasks for today."""

from datetime import date

import click

from taskdog.cli.commands.common_options import filter_options, sort_options
from taskdog.cli.commands.table_helpers import render_table
from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors


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
@sort_options(default_sort="deadline")
@filter_options()
@click.pass_context
@handle_command_errors("displaying tasks")
def today_command(
    ctx: click.Context,
    format: str,
    all: bool,
    status: str | None,
    sort: str,
    reverse: bool,
) -> None:
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

    # Get today's date for filtering
    today = date.today()

    # Get filtered and sorted tasks via API client
    result = ctx_obj.api_client.list_tasks(
        all=all,
        status=status,
        start_date=today,
        end_date=today,
        sort_by=sort,
        reverse=reverse,
    )

    # Render and display
    render_table(ctx_obj, result)
