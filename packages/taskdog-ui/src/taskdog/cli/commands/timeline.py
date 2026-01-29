"""Timeline command - Display actual work times for a day."""

from datetime import date, datetime

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog.presenters.timeline_presenter import TimelinePresenter
from taskdog.renderers.rich_timeline_renderer import RichTimelineRenderer


@click.command(
    name="timeline",
    help="""Display actual work times for a specific day.

Shows when tasks were actually worked on during the day, based on
actual_start and actual_end timestamps. This is a "daily Gantt" view
where the horizontal axis is time-of-day instead of calendar days.

\b
DISPLAY:
  - Horizontal axis: Hours of the day (e.g., 08, 09, 10, ...)
  - Vertical axis: Tasks (sorted by start time)
  - Bars: Show actual work periods with status-based colors
  - Duration: Work time for each task on that day

\b
INCLUDED TASKS:
  - Tasks with actual_start on the target date
  - IN_PROGRESS tasks (uses current time as end)
  - Tasks spanning multiple days (clipped to target date)

\b
COLOR CODING:
  - Blue bars: IN_PROGRESS
  - Green bars: COMPLETED
  - Red bars: CANCELED

\b
EXAMPLE:
  taskdog timeline                    # Show today's work times
  taskdog timeline -d 2026-01-29      # Show specific date
  taskdog timeline --date 2026-01-15  # Show specific date (long form)
""",
)
@click.option(
    "--date",
    "-d",
    "target_date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Date to show timeline for (YYYY-MM-DD). Defaults to today.",
)
@click.pass_context
@handle_command_errors("displaying timeline")
def timeline_command(
    ctx: click.Context,
    target_date: datetime | None,
) -> None:
    """Display actual work times for a specific day.

    Shows a horizontal timeline of when tasks were worked on during the day,
    based on actual_start and actual_end timestamps.
    """
    ctx_obj: CliContext = ctx.obj

    # Default to today if no date specified
    date_to_show = date.today() if target_date is None else target_date.date()

    # Get all tasks (we'll filter by actual_start/end in the presenter)
    # Include all statuses since we want to show completed work too
    task_list = ctx_obj.api_client.list_tasks(
        all=True,  # Include archived to show historical work
        sort_by="id",
        reverse=False,
    )

    # Convert to ViewModel (Presenter filters and prepares data)
    presenter = TimelinePresenter()
    timeline_vm = presenter.present(task_list, date_to_show)

    # Render using Presentation layer
    renderer = RichTimelineRenderer(ctx_obj.console_writer)
    renderer.render(timeline_vm)
