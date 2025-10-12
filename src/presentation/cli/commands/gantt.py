"""Gantt command - Display tasks in Gantt chart format."""

import click
from datetime import datetime, timedelta
from domain.constants import DATETIME_FORMAT
from application.queries.task_query_service import TaskQueryService
from presentation.formatters.rich_gantt_formatter import RichGanttFormatter
from shared.click_types.datetime_with_default import DateTimeWithDefault
from presentation.cli.error_handler import handle_command_errors


def get_previous_monday(from_date=None):
    """Get the previous Monday (or today if today is Monday).

    Args:
        from_date: Optional date to calculate from (defaults to today)

    Returns:
        date object representing the previous Monday
    """
    target_date = from_date or datetime.now().date()
    # weekday(): Monday=0, Sunday=6
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)


@click.command(name="gantt", help="Display tasks in Gantt chart format.")
@click.option(
    "--start-date",
    type=DateTimeWithDefault(),
    help="Start date for the chart (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
)
@click.option(
    "--end-date",
    type=DateTimeWithDefault(),
    help="End date for the chart (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
)
@click.pass_context
@handle_command_errors("displaying Gantt chart")
def gantt_command(ctx, start_date, end_date):
    """Display all tasks as a Gantt chart."""
    repository = ctx.obj["repository"]
    task_query_service = TaskQueryService(repository)

    tasks = task_query_service.get_all_tasks()
    formatter = RichGanttFormatter()

    # Convert datetime strings to date objects if provided
    # Default to previous Monday if start_date not provided
    if start_date:
        start_date_obj = datetime.strptime(start_date, DATETIME_FORMAT).date()
    else:
        start_date_obj = get_previous_monday()

    end_date_obj = None
    if end_date:
        end_date_obj = datetime.strptime(end_date, DATETIME_FORMAT).date()

    output = formatter.format_tasks(tasks, repository, start_date_obj, end_date_obj)
    print(output)
