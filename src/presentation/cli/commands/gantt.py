"""Gantt command - Display tasks in Gantt chart format."""

import click
from datetime import datetime, timedelta
from domain.constants import DATETIME_FORMAT
from domain.entities.task import TaskStatus
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


@click.command(
    name="gantt",
    help="""Display tasks in Gantt chart format with workload analysis.

\b
WORKLOAD CALCULATION:
  The chart displays a "Workload[h]" row at the bottom showing daily workload:
  - Hours are calculated from task estimated_duration
  - Workload is distributed across weekdays only (excludes weekends)
  - Values are rounded up (e.g., 4.3h → 5h)

\b
COLOR CODING:
  - Gray (0h): No workload scheduled
  - Green (1-6h): Normal workload
  - Yellow (6-8h): Near capacity
  - Red (8h+): Overloaded, requires adjustment

\b
TIMELINE SYMBOLS:
  - "░░░" (gray background): Planned period
  - "◆" (colored): Actual progress (status-based color)
  - "◆" (red): Deadline marker
  - " · ": No activity

\b
EXAMPLE:
  taskdog gantt --start-date 2025-10-01 --end-date 2025-10-31

  Shows all tasks with daily workload summary for October 2025.
""",
)
@click.option(
    "--start-date",
    type=DateTimeWithDefault(),
    help="Start date for the chart (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS). Defaults to previous Monday.",
)
@click.option(
    "--end-date",
    type=DateTimeWithDefault(),
    help="End date for the chart (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS). Defaults to last task date.",
)
@click.option(
    "--hide-completed",
    is_flag=True,
    default=False,
    help="Hide completed tasks from the chart.",
)
@click.pass_context
@handle_command_errors("displaying Gantt chart")
def gantt_command(ctx, start_date, end_date, hide_completed):
    """Display all tasks as a Gantt chart with workload analysis.

    The Gantt chart visualizes task timelines and provides daily workload
    analysis to help identify scheduling conflicts and overallocated days.
    """
    repository = ctx.obj["repository"]
    task_query_service = TaskQueryService(repository)

    tasks = task_query_service.get_all_tasks()

    # Filter out completed tasks if requested
    if hide_completed:
        tasks = [task for task in tasks if task.status != TaskStatus.COMPLETED]

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
