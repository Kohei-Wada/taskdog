"""Gantt command - Display tasks in Gantt chart format."""

from datetime import datetime, timedelta

import click

from application.queries.filters.active_filter import ActiveFilter
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.task_query_service import TaskQueryService
from domain.constants import DATETIME_FORMAT
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.renderers.rich_gantt_renderer import RichGanttRenderer
from shared.click_types.datetime_with_default import DateTimeWithDefault


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

By default, shows incomplete tasks only (PENDING, IN_PROGRESS).
Use -a/--all to include completed and failed tasks. Archived tasks are never shown.

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
  taskdog gantt                                  # Show incomplete tasks
  taskdog gantt -a                              # Include completed/failed tasks
  taskdog gantt --start-date 2025-10-01 --end-date 2025-10-31
""",
)
@click.option(
    "--start-date",
    "-s",
    type=DateTimeWithDefault(),
    help="Start date for the chart (YYYY-MM-DD, MM-DD, or MM/DD). Defaults to previous Monday.",
)
@click.option(
    "--end-date",
    "-e",
    type=DateTimeWithDefault(),
    help="End date for the chart (YYYY-MM-DD, MM-DD, or MM/DD). Defaults to last task date.",
)
@click.option(
    "--all",
    "-a",
    "show_all",
    is_flag=True,
    default=False,
    help="Show all active tasks including completed and failed (archived tasks are never shown)",
)
@click.option(
    "--sort",
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
@handle_command_errors("displaying Gantt chart")
def gantt_command(ctx, start_date, end_date, show_all, sort, reverse):
    """Display tasks as a Gantt chart with workload analysis.

    By default, shows incomplete tasks (PENDING, IN_PROGRESS).
    Use -a/--all to include completed and failed tasks.
    Archived tasks are never shown.

    The Gantt chart visualizes task timelines and provides daily workload
    analysis to help identify scheduling conflicts and overallocated days.
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    task_query_service = TaskQueryService(repository)

    # Apply appropriate filter based on --all flag
    # Show all active tasks (exclude archived only) if --all, otherwise show incomplete only
    filter_obj = ActiveFilter() if show_all else IncompleteFilter()

    # Convert datetime strings to date objects if provided
    # Default to previous Monday if start_date not provided
    if start_date:
        start_date_obj = datetime.strptime(start_date, DATETIME_FORMAT).date()
    else:
        start_date_obj = get_previous_monday()

    end_date_obj = None
    if end_date:
        end_date_obj = datetime.strptime(end_date, DATETIME_FORMAT).date()

    # Get Gantt data from Application layer (business logic)
    gantt_result = task_query_service.get_gantt_data(
        filter_obj=filter_obj,
        sort_by=sort,
        reverse=reverse,
        start_date=start_date_obj,
        end_date=end_date_obj,
    )

    # Render using Presentation layer (display logic)
    console_writer = ctx_obj.console_writer
    renderer = RichGanttRenderer(console_writer)
    renderer.render(gantt_result)
