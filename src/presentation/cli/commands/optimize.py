"""Optimize command - Auto-generate optimal task schedules."""

from datetime import datetime, timedelta

import click

from application.services.optimization_summary_builder import OptimizationSummaryBuilder
from application.use_cases.optimize_schedule import OptimizeScheduleInput, OptimizeScheduleUseCase
from domain.constants import DATETIME_FORMAT, DEFAULT_START_HOUR
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.formatters.rich_optimization_formatter import RichOptimizationFormatter
from shared.click_types.datetime_with_default import DateTimeWithDefault


def get_next_weekday():
    """Get the next weekday (skip weekends).

    Returns:
        datetime object representing the next weekday
    """
    today = datetime.now()
    next_day = today + timedelta(days=1)

    # If next day is Saturday (5) or Sunday (6), move to Monday
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)

    # Set time to DEFAULT_START_HOUR (9:00) for schedule start times
    return next_day.replace(hour=DEFAULT_START_HOUR, minute=0, second=0, microsecond=0)


@click.command(
    name="optimize",
    help="""Auto-generate optimal schedules for tasks.

\b
OPTIMIZATION LOGIC:
  The optimizer analyzes all tasks and assigns planned_start/end dates based on:
  - Priority and deadline urgency
  - Estimated duration
  - Task hierarchy (children scheduled before parents)
  - Workload constraints (weekdays only, max hours per day)

\b
CONSTRAINTS:
  - Only schedules tasks with estimated_duration set
  - Skips tasks with existing planned_start (unless --force)
  - Distributes workload across weekdays only
  - Respects max hours per day (default: 6h)
  - Parent task periods encompass all children

\b
OPTIONS:
  --start-date DATE       Start date for scheduling (default: next weekday)
  --max-hours-per-day N   Maximum work hours per day (default: 6.0)
  --force                 Override existing schedules
  --dry-run               Preview changes without saving

\b
EXAMPLES:
  # Optimize all unscheduled tasks
  taskdog optimize

  # Start scheduling from specific date with 8h/day limit
  taskdog optimize --start-date 2025-10-15 --max-hours-per-day 8

  # Preview optimization without saving
  taskdog optimize --dry-run

  # Re-optimize all tasks (including already scheduled)
  taskdog optimize --force
""",
)
@click.option(
    "--start-date",
    type=DateTimeWithDefault(default_hour=DEFAULT_START_HOUR),
    help="Start date for scheduling (YYYY-MM-DD, MM-DD, or MM/DD; defaults to 09:00:00). Defaults to next weekday.",
)
@click.option(
    "--max-hours-per-day",
    "-m",
    type=float,
    default=6.0,
    help="Maximum work hours per day (default: 6.0)",
)
@click.option(
    "--force", "-f", is_flag=True, default=False, help="Override existing schedules for all tasks"
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Preview changes without saving to database"
)
@click.pass_context
@handle_command_errors("optimizing schedules")
def optimize_command(ctx, start_date, max_hours_per_day, force, dry_run):
    """Auto-generate optimal schedules for tasks.

    Analyzes all tasks and assigns planned_start/end dates based on
    priorities, deadlines, estimated durations, and workload constraints.
    """
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository

    # Parse start_date or use next weekday
    start_dt = datetime.strptime(start_date, DATETIME_FORMAT) if start_date else get_next_weekday()

    # Validate max_hours_per_day
    if max_hours_per_day <= 0:
        console.print("[red]Error:[/red] max-hours-per-day must be positive")
        return

    # Get all tasks before optimization to track changes
    all_tasks_before = repository.get_all()
    task_states_before = {t.id: t.planned_start for t in all_tasks_before}

    # Create input DTO
    input_dto = OptimizeScheduleInput(
        start_date=start_dt,
        max_hours_per_day=max_hours_per_day,
        force_override=force,
        dry_run=dry_run,
    )

    # Execute optimization
    use_case = OptimizeScheduleUseCase(repository)
    modified_tasks, daily_allocations = use_case.execute(input_dto)

    # Display results
    if not modified_tasks:
        console.print("[yellow]No tasks were optimized.[/yellow]")
        console.print("\nPossible reasons:")
        console.print("  - All tasks already have schedules (use --force to override)")
        console.print("  - No tasks have estimated_duration set")
        console.print("  - All tasks are completed")
        return

    # Calculate summary
    summary_builder = OptimizationSummaryBuilder(repository)
    summary = summary_builder.build(
        modified_tasks, task_states_before, daily_allocations, max_hours_per_day
    )

    # Show summary header
    if dry_run:
        console.print(
            f"[cyan]DRY RUN:[/cyan] Preview of {len(modified_tasks)} task(s) to be optimized\n"
        )
    else:
        console.print(f"[green]✓[/green] Optimized schedules for {len(modified_tasks)} task(s)\n")

    # Format and print table
    formatter = RichOptimizationFormatter(console)
    formatter.format_table(modified_tasks, task_states_before)

    # Show summary section
    formatter.format_summary(summary)

    # Show warnings
    formatter.format_warnings(summary, max_hours_per_day)

    # Show configuration
    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  Start date: {start_dt.strftime(DATETIME_FORMAT)}")
    console.print(f"  Max hours/day: {max_hours_per_day}h")
    console.print(f"  Force override: {force}")

    if dry_run:
        console.print("\n[yellow]Note:[/yellow] Changes not saved. Remove --dry-run to apply.")
