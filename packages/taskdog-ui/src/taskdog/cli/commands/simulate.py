"""Simulate command - Predict task completion dates without saving to database."""

from datetime import date, datetime

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog.console.console_writer import ConsoleWriter
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault
from taskdog_core.application.dto.simulation_result import SimulationResult


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
    if result.best_algorithm:
        console_writer.print(
            f"  Best Algorithm: {result.best_algorithm} "
            f"({result.successful_algorithms}/{result.total_algorithms_tested} succeeded)"
        )
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
    console_writer.print("  • Complete or cancel existing tasks to free up capacity")


@click.command(
    name="simulate",
    help="""Simulate a virtual task to predict completion date without saving to database.

This command runs optimization with a virtual task to help you answer:
"When can I complete this new task?" - Perfect for deadline negotiation.

Uses the same interface as 'add' command for consistency.
""",
)
@click.argument("name", type=str)
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
    default=None,
    help="Task priority (default: from config or 5)",
)
@click.option(
    "--deadline",
    "-D",
    type=DateTimeWithDefault(),
    help="Task deadline (same format as add command)",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    type=str,
    help="Tags for categorization (can be specified multiple times)",
)
@click.option(
    "--depends-on",
    "-d",
    multiple=True,
    type=int,
    help="Task IDs this task depends on (can be specified multiple times)",
)
@click.option(
    "--fixed",
    "-f",
    is_flag=True,
    help="Mark task as fixed (won't be rescheduled)",
)
@click.option(
    "--max-hours-per-day",
    "-m",
    type=click.FloatRange(min=0, min_open=True, max=24.0),
    default=None,
    help="Max work hours per day (default: from config or 6.0)",
)
@click.pass_context
@handle_command_errors("simulating task")
def simulate_command(
    ctx: click.Context,
    name: str,
    estimate: float,
    priority: int | None,
    deadline: datetime | None,
    tag: tuple[str, ...],
    depends_on: tuple[int, ...],
    fixed: bool,
    max_hours_per_day: float | None,
) -> None:
    """Simulate a virtual task to predict completion date.

    Usage:
        # Basic simulation (same as add command)
        taskdog simulate "Fix bug" -e 8

        # With priority and deadline
        taskdog simulate "New feature" -e 16 -p 10 -D 2025-12-25

        # With tags and dependencies (same as add)
        taskdog simulate "Deploy" -e 4 -t deployment -d 123

        # With capacity constraint
        taskdog simulate "Refactoring" -e 30 -m 8
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    api_client = ctx_obj.api_client
    config = ctx_obj.config

    # Use config defaults if not provided
    if priority is None:
        priority = config.task.default_priority
    if max_hours_per_day is None:
        max_hours_per_day = config.optimization.max_hours_per_day

    # Execute simulation via API
    result = api_client.simulate_task(
        estimated_duration=estimate,
        priority=priority,
        name=name,
        deadline=deadline,
        depends_on=list(depends_on) if depends_on else None,
        tags=list(tag) if tag else None,
        is_fixed=fixed,
        max_hours_per_day=max_hours_per_day,
    )

    # Display result
    if result.is_schedulable:
        _show_success_result(console_writer, result)
    else:
        _show_failure_result(console_writer, result)
