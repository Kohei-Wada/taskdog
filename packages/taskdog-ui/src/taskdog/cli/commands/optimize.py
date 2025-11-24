"""Optimize command - Auto-generate optimal task schedules."""

from datetime import datetime

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog.console.console_writer import ConsoleWriter
from taskdog.constants.ui_defaults import DEFAULT_START_HOUR
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault
from taskdog_core.application.dto.optimization_output import OptimizationOutput
from taskdog_core.shared.utils.date_utils import get_next_weekday


def _show_failed_tasks(
    console_writer: ConsoleWriter, result: OptimizationOutput
) -> None:
    """Show details of failed tasks.

    Args:
        console_writer: Console writer for output
        result: Optimization result containing failed tasks
    """
    console_writer.empty_line()
    for failure in result.failed_tasks:
        console_writer.print(f"  Task {failure.task.id}: {failure.task.name}")
        console_writer.print(f"  → {failure.reason}")


def _show_no_tasks_message(console_writer: ConsoleWriter) -> None:
    """Show message when no tasks were optimized.

    Args:
        console_writer: Console writer for output
    """
    console_writer.warning("No tasks were optimized.")
    console_writer.print("\nPossible reasons:")
    console_writer.print(
        "  - All tasks already have schedules (use --force to override)"
    )
    console_writer.print("  - No tasks have estimated_duration set")
    console_writer.print("  - All tasks are completed")


@click.command(
    name="optimize",
    help="""Auto-generate optimal schedules for tasks based on priority, deadlines, and workload.

Schedules tasks with estimated_duration across weekdays, respecting max hours/day.
Use --force to override existing schedules.

Examples:
  taskdog optimize                    # Optimize all schedulable tasks
  taskdog optimize 1 2 3              # Optimize only tasks 1, 2, and 3
  taskdog optimize 5 --force          # Force optimize task 5
""",
)
@click.argument("task_ids", nargs=-1, type=int, required=False)
@click.option(
    "--start-date",
    type=DateTimeWithDefault("start"),
    help="Start date for scheduling (default: next weekday at 09:00)",
)
@click.option(
    "--max-hours-per-day",
    "-m",
    type=click.FloatRange(min=0, min_open=True, max=24.0),
    default=None,
    help="Max work hours per day (default: from config or 6.0)",
)
@click.option(
    "--algorithm",
    "-a",
    type=str,
    default=None,
    help=(
        "Optimization algorithm (default: from config or greedy): "
        "greedy (front-load), "
        "balanced (even distribution), "
        "backward (JIT from deadline), "
        "priority_first (priority only), "
        "earliest_deadline (EDF), "
        "round_robin (parallel progress), "
        "dependency_aware (CPM), "
        "genetic (evolutionary), "
        "monte_carlo (random sampling)"
    ),
)
@click.option("--force", "-f", is_flag=True, help="Override existing schedules")
@click.pass_context
@handle_command_errors("optimizing schedules")
def optimize_command(
    ctx: click.Context,
    task_ids: tuple[int, ...],
    start_date: datetime | None,
    max_hours_per_day: float | None,
    algorithm: str | None,
    force: bool,
) -> None:
    """Auto-generate optimal schedules for tasks."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    api_client = ctx_obj.api_client

    # Use start_date or get next weekday with default business start hour
    start_date = start_date if start_date else get_next_weekday(DEFAULT_START_HOUR)

    # Convert task_ids tuple to list (or None if empty)
    task_ids_list = list(task_ids) if task_ids else None

    # Execute optimization via API
    # Server will apply config defaults for None values
    result = api_client.optimize_schedule(
        algorithm=algorithm,  # None if not provided, server applies default
        start_date=start_date,
        max_hours_per_day=max_hours_per_day,  # None if not provided, server applies default
        force_override=force,
        task_ids=task_ids_list,
    )

    # Handle empty result (no tasks to optimize)
    if result.all_failed():
        console_writer.warning("All tasks failed to be scheduled.")
        _show_failed_tasks(console_writer, result)
        return

    if len(result.successful_tasks) == 0:
        _show_no_tasks_message(console_writer)
        return

    # Show success/partial success summary
    success_count = len(result.successful_tasks)
    if result.has_failures():
        failed_count = len(result.failed_tasks)
        console_writer.warning(
            f"Optimized {success_count} task(s) using '{algorithm}' "
            f"({failed_count} could not be scheduled)"
        )
        _show_failed_tasks(console_writer, result)
    else:
        console_writer.success(
            f"Optimized {success_count} task(s) using '{algorithm}' (all tasks scheduled)"
        )
