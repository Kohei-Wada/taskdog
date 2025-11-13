"""Gantt command - Display tasks in Gantt chart format."""

import click

from taskdog.cli.commands.common_options import filter_options, sort_options
from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog.presenters.gantt_presenter import GanttPresenter
from taskdog.renderers.rich_gantt_renderer import RichGanttRenderer
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault
from taskdog_core.shared.utils.date_utils import get_previous_monday


@click.command(
    name="gantt",
    help="""Display tasks in Gantt chart format with workload analysis.

By default, shows non-archived tasks (all statuses except archived).
Use -a/--all to include archived tasks.
Use --status to filter by specific status (overrides --all).
Use --tag to filter by tags (OR logic when multiple tags specified).

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
  taskdog gantt                                  # Show non-archived tasks
  taskdog gantt -a                              # Show all tasks (including archived)
  taskdog gantt --status completed              # Show only completed tasks
  taskdog gantt -t work -t urgent               # Tasks with tag "work" OR "urgent"
  taskdog gantt --start-date 2025-10-01 --end-date 2025-10-31
""",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    type=str,
    help="Filter by tags (can be specified multiple times, uses OR logic)",
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
@sort_options(default_sort="deadline")
@filter_options()
@click.pass_context
@handle_command_errors("displaying Gantt chart")
def gantt_command(ctx, tag, start_date, end_date, all, status, sort, reverse):
    """Display tasks as a Gantt chart with workload analysis.

    By default, shows non-archived tasks (all statuses except archived).
    Use -a/--all to include all tasks (including archived).
    Use --status to filter by specific status (overrides --all).
    Use --tag to filter by tags (OR logic when multiple tags specified).

    The Gantt chart visualizes task timelines and provides daily workload
    analysis to help identify scheduling conflicts and overallocated days.
    """
    ctx_obj: CliContext = ctx.obj

    # Prepare filter parameters (tags use OR logic by default)
    tags = list(tag) if tag else None

    # Convert datetime to date objects if provided (DateTimeWithDefault returns datetime)
    # Default to previous Monday if start_date not provided
    start_date_obj = start_date.date() if start_date else get_previous_monday()

    end_date_obj = end_date.date() if end_date else None

    # Get Gantt data via API client
    gantt_result = ctx_obj.api_client.get_gantt_data(
        all=all,
        status=status,
        tags=tags,
        sort_by=sort,
        reverse=reverse,
        start_date=start_date_obj,
        end_date=end_date_obj,
        holiday_checker=ctx_obj.holiday_checker,
    )

    # Convert DTO to ViewModel (Presenter applies presentation logic)
    presenter = GanttPresenter()
    gantt_view_model = presenter.present(gantt_result)

    # Render using Presentation layer (display logic)
    console_writer = ctx_obj.console_writer
    renderer = RichGanttRenderer(console_writer)
    renderer.render(gantt_view_model)
