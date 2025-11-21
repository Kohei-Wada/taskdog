"""Simulate command - Predict task completion dates without saving to database."""

from datetime import date, datetime

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog.console.console_writer import ConsoleWriter
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault
from taskdog_core.application.dto.simulation_result import SimulationResult
from taskdog_core.shared.utils.date_utils import get_next_weekday


def _format_datetime(dt: datetime | None) -> str:
    """Format datetime for display.

    Args:
        dt: Datetime to format

    Returns:
        Formatted datetime string or "N/A"
    """
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M")


def _format_date(d: date | None) -> str:
    """Format date for display.

    Args:
        d: Date to format

    Returns:
        Formatted date string or "N/A"
    """
    if d is None:
        return "N/A"
    return d.strftime("%Y-%m-%d")


def _show_success_result(
    console_writer: ConsoleWriter, result: SimulationResult
) -> None:
    """Show simulation result when task can be scheduled.

    Args:
        console_writer: Console writer for output
        result: Simulation result
    """
    console_writer.success(
        f"Task can be scheduled: {_format_datetime(result.planned_start)} → {_format_datetime(result.planned_end)}"
    )
    console_writer.empty_line()

    # Task Details
    console_writer.print("[bold]Task Details:[/bold]")
    console_writer.print(f"  Name: {result.virtual_task_name}")
    console_writer.print(f"  Estimated: {result.estimated_duration} hours")
    console_writer.print(f"  Priority: {result.priority}")
    if result.deadline:
        console_writer.print(f"  Deadline: {_format_datetime(result.deadline)}")
    console_writer.empty_line()

    # Schedule
    console_writer.print("[bold]Schedule:[/bold]")
    console_writer.print(f"  Planned Start: {_format_datetime(result.planned_start)}")
    console_writer.print(f"  Planned End: {_format_datetime(result.planned_end)}")
    console_writer.empty_line()

    # Workload Analysis
    console_writer.print("[bold]Workload Analysis:[/bold]")
    console_writer.print(
        f"  Peak: {result.peak_workload:.1f}h on {_format_date(result.peak_date)}"
    )
    console_writer.print(f"  Average: {result.average_workload:.1f}h/day")
    console_writer.print(f"  Total Days: {result.total_workload_days}")


def _show_failure_result(
    console_writer: ConsoleWriter, result: SimulationResult
) -> None:
    """Show simulation result when task cannot be scheduled.

    Args:
        console_writer: Console writer for output
        result: Simulation result
    """
    console_writer.error(
        "Task cannot be scheduled", Exception(result.failure_reason or "Unknown error")
    )
    console_writer.empty_line()

    # Task Details
    console_writer.print("[bold]Task Details:[/bold]")
    console_writer.print(f"  Name: {result.virtual_task_name}")
    console_writer.print(f"  Estimated: {result.estimated_duration} hours")
    console_writer.print(f"  Priority: {result.priority}")
    if result.deadline:
        console_writer.print(f"  Deadline: {_format_datetime(result.deadline)}")
    console_writer.empty_line()

    console_writer.print("[yellow]Suggestions:[/yellow]")
    console_writer.print("  • Adjust the deadline")
    console_writer.print("  • Increase max-hours-per-day")
    console_writer.print("  • Use --force to override existing schedules")
    console_writer.print("  • Try a different optimization algorithm")


@click.command(
    name="simulate",
    help="""Simulate a virtual task to predict completion date without saving to database.

This command runs optimization with a virtual task to help you answer:
"When can I complete this new task?" - Perfect for deadline negotiation.
""",
)
@click.option(
    "--estimate",
    "-e",
    type=click.FloatRange(min=0, min_open=True),
    required=True,
    help="Estimated duration in hours (required)",
)
@click.option(
    "--priority",
    "-p",
    type=click.IntRange(min=1),
    default=5,
    help="Task priority (default: 5)",
)
@click.option(
    "--name",
    "-n",
    type=str,
    default="Simulated Task",
    help='Task name for display (default: "Simulated Task")',
)
@click.option(
    "--deadline",
    "-d",
    type=DateTimeWithDefault("end"),
    help="Optional deadline for the task",
)
@click.option(
    "--algorithm",
    "-a",
    type=str,
    default=None,
    help=(
        "Optimization algorithm (default: from config or greedy): "
        "greedy, balanced, backward, priority_first, earliest_deadline, "
        "round_robin, dependency_aware, genetic, monte_carlo"
    ),
)
@click.option(
    "--max-hours-per-day",
    "-m",
    type=click.FloatRange(min=0, min_open=True, max=24.0),
    default=None,
    help="Max work hours per day (default: from config or 6.0)",
)
@click.option(
    "--start-date",
    type=DateTimeWithDefault("start"),
    help="Start date for scheduling (default: next weekday at 09:00)",
)
@click.option("--force", "-f", is_flag=True, help="Override existing schedules")
@click.pass_context
@handle_command_errors("simulating task")
def simulate_command(
    ctx: click.Context,
    estimate: float,
    priority: int,
    name: str,
    deadline: datetime | None,
    algorithm: str | None,
    max_hours_per_day: float | None,
    start_date: datetime | None,
    force: bool,
) -> None:
    """Simulate a virtual task to predict completion date."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    api_client = ctx_obj.api_client
    config = ctx_obj.config

    # Use config defaults if not provided
    if algorithm is None:
        algorithm = config.optimization.default_algorithm
    if max_hours_per_day is None:
        max_hours_per_day = config.optimization.max_hours_per_day
    if start_date is None:
        start_date = get_next_weekday(config.time.default_start_hour)

    # Execute simulation via API
    result = api_client.simulate_task(
        estimated_duration=estimate,
        priority=priority,
        name=name,
        deadline=deadline,
        algorithm=algorithm,
        max_hours_per_day=max_hours_per_day,
        start_date=start_date,
        force_override=force,
    )

    # Display result
    if result.is_schedulable:
        _show_success_result(console_writer, result)
    else:
        _show_failure_result(console_writer, result)
