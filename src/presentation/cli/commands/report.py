"""Report command - Generate markdown workload report grouped by date."""

from collections import defaultdict
from datetime import date

import click

from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task
from presentation.cli.commands.common_options import (
    date_range_options,
    filter_options,
    sort_options,
)
from presentation.cli.commands.filter_helpers import build_task_filter
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors


@click.command(
    name="report",
    help="""Generate markdown workload report grouped by date.

This command generates a markdown table showing tasks grouped by date with their allocated hours.
Only tasks that have been scheduled by the optimizer (with daily_allocations) are included.

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
""",
)
@date_range_options()
@sort_options(default_sort="planned_start")
@filter_options()
@click.pass_context
@handle_command_errors("generating report")
def report_command(ctx, start_date, end_date, all, status, sort, reverse):
    """Generate markdown workload report grouped by date.

    Shows only tasks with daily_allocations (scheduled by optimizer).
    Groups tasks by date and displays allocated hours for each day.
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    task_query_service = TaskQueryService(repository)

    # Apply filter based on options (priority: --status > --all > default)
    filter_obj = build_task_filter(all=all, status=status)

    # Get filtered and sorted tasks
    tasks = task_query_service.get_filtered_tasks(
        filter_obj=filter_obj, sort_by=sort, reverse=reverse
    )

    # Filter to only tasks with daily_allocations
    scheduled_tasks = [task for task in tasks if task.daily_allocations]

    if not scheduled_tasks:
        console_writer = ctx_obj.console_writer
        console_writer.warning(
            "No scheduled tasks found. Run 'taskdog optimize' to schedule tasks."
        )
        return

    # Convert datetime to date objects for filtering
    start_date_obj = start_date.date() if start_date else None
    end_date_obj = end_date.date() if end_date else None

    # Group tasks by date (using daily_allocations)
    grouped_tasks = _group_tasks_by_date(scheduled_tasks, start_date_obj, end_date_obj)

    if not grouped_tasks:
        console_writer = ctx_obj.console_writer
        console_writer.warning(
            "No tasks found in the specified date range. Try adjusting --start-date or --end-date."
        )
        return

    # Generate markdown report
    markdown = _generate_markdown_report(grouped_tasks)

    # Output to console (disable markup to preserve markdown special characters like [])
    console_writer = ctx_obj.console_writer
    console_writer.print(markdown, markup=False)


def _group_tasks_by_date(
    tasks: list[Task],
    start_date: date | None,
    end_date: date | None,
) -> dict[date, list[tuple[Task, float]]]:
    """Group tasks by date using daily_allocations.

    Args:
        tasks: List of tasks with daily_allocations
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        Dictionary mapping date to list of (task, allocated_hours) tuples, sorted by date
    """
    grouped: dict[date, list[tuple[Task, float]]] = defaultdict(list)

    for task in tasks:
        if not task.daily_allocations:
            continue

        for task_date, allocated_hours in task.daily_allocations.items():
            # Apply date range filter
            if start_date and task_date < start_date:
                continue
            if end_date and task_date > end_date:
                continue

            grouped[task_date].append((task, allocated_hours))

    # Sort by date
    return dict(sorted(grouped.items()))


def _generate_markdown_report(grouped_tasks: dict[date, list[tuple[Task, float]]]) -> str:
    """Generate markdown formatted report.

    Args:
        grouped_tasks: Dictionary mapping date to list of (task, allocated_hours) tuples

    Returns:
        Markdown formatted report string
    """
    lines = []

    for task_date, task_hours_list in grouped_tasks.items():
        # Date header in Japanese format (YYYY/MM/DD)
        lines.append(f"{task_date.strftime('%Y/%m/%d')}")

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
