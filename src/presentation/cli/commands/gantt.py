"""Gantt command - Display tasks in Gantt chart format."""

import click
from datetime import datetime
from presentation.formatters.rich_gantt_formatter import RichGanttFormatter
from shared.click_types.datetime_with_default import DateTimeWithDefault


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
def gantt_command(ctx, start_date, end_date):
    """Display all tasks as a Gantt chart."""
    repository = ctx.obj["repository"]
    task_query_service = ctx.obj["task_query_service"]

    try:
        tasks = task_query_service.get_all_tasks()
        formatter = RichGanttFormatter()

        # Convert datetime strings to date objects if provided
        start_date_obj = None
        end_date_obj = None
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").date()

        output = formatter.format_tasks(tasks, repository, start_date_obj, end_date_obj)
        print(output)
    except Exception as e:
        print(f"Error displaying Gantt chart: {e}")
