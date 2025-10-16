"""Optimize command - Auto-generate optimal task schedules."""

from datetime import datetime

import click

from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.services.optimization_summary_builder import OptimizationSummaryBuilder
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from domain.constants import DATETIME_FORMAT, DEFAULT_START_HOUR
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.formatters.rich_gantt_formatter import RichGanttFormatter
from presentation.formatters.rich_optimization_formatter import RichOptimizationFormatter
from shared.click_types.datetime_with_default import DateTimeWithDefault
from shared.utils.date_utils import get_next_weekday


@click.command(
    name="optimize",
    help="""Auto-generate optimal schedules for tasks based on priority, deadlines, and workload.

Schedules tasks with estimated_duration across weekdays, respecting max hours/day.
Use --force to override existing schedules, --dry-run to preview changes.
""",
)
@click.option(
    "--start-date",
    type=DateTimeWithDefault(default_hour=DEFAULT_START_HOUR),
    help="Start date for scheduling (default: next weekday at 09:00)",
)
@click.option(
    "--max-hours-per-day",
    "-m",
    type=click.FloatRange(min=0, min_open=True, max=24.0),
    default=6.0,
    help="Max work hours per day (default: 6.0)",
)
@click.option(
    "--algorithm",
    "-a",
    type=str,
    default="greedy",
    help=(
        "Optimization algorithm: "
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
@click.option("--dry-run", "-d", is_flag=True, help="Preview without saving")
@click.pass_context
@handle_command_errors("optimizing schedules")
def optimize_command(ctx, start_date, max_hours_per_day, algorithm, force, dry_run):
    """Auto-generate optimal schedules for tasks."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository

    # Parse start_date or use next weekday
    start_dt = datetime.strptime(start_date, DATETIME_FORMAT) if start_date else get_next_weekday()

    # Get all tasks before optimization to track changes
    all_tasks_before = repository.get_all()
    task_states_before = {t.id: t.planned_start for t in all_tasks_before}

    # Create input DTO
    input_dto = OptimizeScheduleInput(
        start_date=start_dt,
        max_hours_per_day=max_hours_per_day,
        force_override=force,
        dry_run=dry_run,
        algorithm_name=algorithm,
    )

    # Execute optimization
    use_case = OptimizeScheduleUseCase(repository)
    modified_tasks, daily_allocations = use_case.execute(input_dto)

    # Display results
    if not modified_tasks:
        console_writer.print_warning("No tasks were optimized.")
        console_writer.print("\nPossible reasons:")
        console_writer.print("  - All tasks already have schedules (use --force to override)")
        console_writer.print("  - No tasks have estimated_duration set")
        console_writer.print("  - All tasks are completed")
        return

    # Calculate summary
    summary_builder = OptimizationSummaryBuilder(repository)
    summary = summary_builder.build(
        modified_tasks, task_states_before, daily_allocations, max_hours_per_day
    )

    # Show summary header
    console_writer.print_optimization_result(len(modified_tasks), dry_run)

    # Format and print Gantt chart
    gantt_formatter = RichGanttFormatter()
    gantt_output = gantt_formatter.format_tasks(modified_tasks, repository)
    print(gantt_output)

    # Create optimization formatter for summary and warnings
    formatter = RichOptimizationFormatter(console_writer)

    # Show summary section
    formatter.format_summary(summary)

    # Show warnings
    formatter.format_warnings(summary, max_hours_per_day)

    # Show configuration
    console_writer.print_optimization_heading()
    console_writer.print(f"  Algorithm: {algorithm}")
    console_writer.print(f"  Start date: {start_dt.strftime(DATETIME_FORMAT)}")
    console_writer.print(f"  Max hours/day: {max_hours_per_day}h")
    console_writer.print(f"  Force override: {force}")

    if dry_run:
        print("\n")  # Add spacing
        console_writer.print_info("Changes not saved. Remove --dry-run to apply.")
