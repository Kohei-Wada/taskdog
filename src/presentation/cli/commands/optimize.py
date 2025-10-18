"""Optimize command - Auto-generate optimal task schedules."""

from datetime import datetime

import click

from application.dto.optimization_result import OptimizationResult
from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from domain.constants import DATETIME_FORMAT
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.console.console_writer import ConsoleWriter
from shared.click_types.datetime_with_default import DateTimeWithDefault
from shared.utils.date_utils import get_next_weekday


def _show_failed_tasks(console_writer: ConsoleWriter, result: OptimizationResult) -> None:
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
    console_writer.print("  - All tasks already have schedules (use --force to override)")
    console_writer.print("  - No tasks have estimated_duration set")
    console_writer.print("  - All tasks are completed")


@click.command(
    name="optimize",
    help="""Auto-generate optimal schedules for tasks based on priority, deadlines, and workload.

Schedules tasks with estimated_duration across weekdays, respecting max hours/day.
Use --force to override existing schedules.
""",
)
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
def optimize_command(ctx, start_date, max_hours_per_day, algorithm, force):
    """Auto-generate optimal schedules for tasks."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    config = ctx_obj.config

    # Parse start_date or use next weekday
    start_date = (
        datetime.strptime(start_date, DATETIME_FORMAT) if start_date else get_next_weekday()
    )

    # Use config defaults if not provided via CLI
    if max_hours_per_day is None:
        max_hours_per_day = config.optimization.max_hours_per_day
    if algorithm is None:
        algorithm = config.optimization.default_algorithm

    # Execute optimization
    use_case = OptimizeScheduleUseCase(repository, config)
    result = use_case.execute(
        OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            force_override=force,
            algorithm_name=algorithm,
        )
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
        console_writer.print_success(
            f"Optimized {success_count} task(s) using '{algorithm}' (all tasks scheduled)"
        )
