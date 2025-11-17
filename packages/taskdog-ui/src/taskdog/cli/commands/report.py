"""Report command - Generate markdown workload report grouped by date."""

from collections import defaultdict
from datetime import date

import click

from taskdog.cli.commands.common_options import (
    date_range_options,
    filter_options,
    sort_options,
)
from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog_core.application.dto.task_dto import GanttTaskDto


@click.command(
    name="report",
    help="""Generate markdown workload report grouped by date.

This command generates a markdown table showing tasks grouped by date with their allocated hours.
Includes all scheduled work: optimized tasks, manually scheduled tasks, and fixed tasks.

The output is formatted for easy copying to Notion or other documentation tools.

\b
EXAMPLE OUTPUT:
  2025/10/30
  |タスク|想定工数[h]|
  |--|--|
  |task1|3|
  |task2|3|
  |sum|6|

\b
USAGE:
  taskdog report                                 # All scheduled tasks
  taskdog report --start-date 2025-10-01        # Tasks from Oct 1st onwards
  taskdog report --start-date 10-01 --end-date 10-31  # Tasks in October
  taskdog report --status pending               # Only pending scheduled tasks
  taskdog report -t work -t urgent              # Tasks with tag "work" OR "urgent"
""",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    type=str,
    help="Filter by tags (can be specified multiple times, uses OR logic)",
)
@date_range_options()
@sort_options(default_sort="planned_start")
@filter_options()
@click.pass_context
@handle_command_errors("generating report")
def report_command(ctx, tag, start_date, end_date, all, status, sort, reverse):
    """Generate markdown workload report grouped by date.

    Shows all scheduled work including optimized tasks, manually scheduled tasks, and fixed tasks.
    Groups tasks by date and displays allocated hours for each day.
    """
    ctx_obj: CliContext = ctx.obj
    api_client = ctx_obj.api_client

    # Prepare filter parameters (tags use OR logic by default)
    tags = list(tag) if tag else None

    # Convert datetime to date objects for filtering
    start_date_obj = start_date.date() if start_date else None
    end_date_obj = end_date.date() if end_date else None

    # Get Gantt data via API (includes pre-calculated task_daily_hours)
    gantt_result = api_client.get_gantt_data(
        all=all,
        status=status,
        tags=tags,
        filter_start_date=start_date_obj,
        filter_end_date=end_date_obj,
        sort_by=sort,
        reverse=reverse,
    )

    # Group tasks by date using pre-calculated daily hours
    grouped_tasks = _group_tasks_by_date(
        gantt_result.tasks,
        gantt_result.task_daily_hours,
        start_date_obj,
        end_date_obj,
    )

    if not grouped_tasks:
        console_writer = ctx_obj.console_writer
        console_writer.warning(
            "No scheduled tasks found. Try adjusting --start-date or --end-date, or run 'taskdog optimize' to schedule tasks."
        )
        return

    # Generate markdown report
    markdown = _generate_markdown_report(grouped_tasks)

    # Output to console (disable markup to preserve markdown special characters like [])
    console_writer = ctx_obj.console_writer
    console_writer.print(markdown, markup=False)


def _group_tasks_by_date(
    tasks: list[GanttTaskDto],
    task_daily_hours: dict[int, dict[date, float]],
    start_date: date | None,
    end_date: date | None,
) -> dict[date, list[tuple[GanttTaskDto, float]]]:
    """Group tasks by date using pre-calculated daily hours.

    Args:
        tasks: List of tasks to group
        task_daily_hours: Pre-calculated daily hours per task (task.id -> {date: hours})
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        Dictionary mapping date to list of (task, allocated_hours) tuples, sorted by date
    """
    grouped: dict[date, list[tuple[GanttTaskDto, float]]] = defaultdict(list)

    for task in tasks:
        # Get pre-calculated daily hours for this task
        daily_hours = task_daily_hours.get(task.id, {})

        if not daily_hours:
            continue

        for task_date, allocated_hours in daily_hours.items():
            # Apply date range filter
            if start_date and task_date < start_date:
                continue
            if end_date and task_date > end_date:
                continue

            grouped[task_date].append((task, allocated_hours))

    # Sort by date
    return dict(sorted(grouped.items()))


def _generate_markdown_report(
    grouped_tasks: dict[date, list[tuple[GanttTaskDto, float]]],
) -> str:
    """Generate markdown formatted report.

    Args:
        grouped_tasks: Dictionary mapping date to list of (task, allocated_hours) tuples

    Returns:
        Markdown formatted report string
    """
    lines = []

    for task_date, task_hours_list in grouped_tasks.items():
        # Date header in Japanese format (YYYY/MM/DD)
        lines.append(f"{DateTimeFormatter.format_date_japanese(task_date)}")

        # Table header
        lines.append("|タスク|想定工数[h]|")
        lines.append("|--|--|")

        # Task rows
        total_hours = 0.0
        for task, allocated_hours in task_hours_list:
            if allocated_hours > 0:
                # Display allocated hours as integer
                lines.append(f"|{task.name}|{int(allocated_hours)}|")
                total_hours += allocated_hours
            else:
                # Display "-" for tasks with no allocation
                lines.append(f"|{task.name}|-|")

        # Sum row
        if total_hours > 0:
            lines.append(f"|sum|{int(total_hours)}|")
        else:
            lines.append("|sum|-|")

        # Empty line between dates
        lines.append("")

    return "\n".join(lines)
