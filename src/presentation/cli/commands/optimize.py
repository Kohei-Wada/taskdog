"""Optimize command - Auto-generate optimal task schedules."""

from datetime import datetime, timedelta

import click
from rich.table import Table

from application.use_cases.optimize_schedule import OptimizeScheduleInput, OptimizeScheduleUseCase
from domain.constants import DATETIME_FORMAT
from presentation.cli.error_handler import handle_command_errors
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

    # Set time to 18:00:00 for consistency with DateTimeWithDefault
    return next_day.replace(hour=18, minute=0, second=0, microsecond=0)


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
    type=DateTimeWithDefault(default_hour=9),
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
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]

    # Parse start_date or use next weekday
    if start_date:
        start_dt = datetime.strptime(start_date, DATETIME_FORMAT)
    else:
        start_dt = get_next_weekday()

    # Validate max_hours_per_day
    if max_hours_per_day <= 0:
        console.print("[red]Error:[/red] max-hours-per-day must be positive")
        return

    # Create input DTO
    input_dto = OptimizeScheduleInput(
        start_date=start_dt,
        max_hours_per_day=max_hours_per_day,
        force_override=force,
        dry_run=dry_run,
    )

    # Execute optimization
    use_case = OptimizeScheduleUseCase(repository)
    modified_tasks = use_case.execute(input_dto)

    # Display results
    if not modified_tasks:
        console.print("[yellow]No tasks were optimized.[/yellow]")
        console.print("\nPossible reasons:")
        console.print("  - All tasks already have schedules (use --force to override)")
        console.print("  - No tasks have estimated_duration set")
        console.print("  - All tasks are completed")
        return

    # Show summary
    if dry_run:
        console.print(
            f"[cyan]DRY RUN:[/cyan] Preview of {len(modified_tasks)} task(s) to be optimized\n"
        )
    else:
        console.print(f"[green]✓[/green] Optimized schedules for {len(modified_tasks)} task(s)\n")

    # Create table
    table = Table(title="Optimized Tasks")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="white")
    table.add_column("Priority", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Planned Start", style="green")
    table.add_column("Planned End", style="green")
    table.add_column("Deadline", style="red")

    # Sort by planned_start
    sorted_tasks = sorted(modified_tasks, key=lambda t: t.planned_start if t.planned_start else "")

    for task in sorted_tasks:
        # Format duration
        duration_str = f"{task.estimated_duration}h" if task.estimated_duration else "-"

        # Format dates
        start_str = task.planned_start if task.planned_start else "-"
        end_str = task.planned_end if task.planned_end else "-"
        deadline_str = task.deadline if task.deadline else "-"

        table.add_row(
            str(task.id),
            task.name,
            str(task.priority),
            duration_str,
            start_str,
            end_str,
            deadline_str,
        )

    console.print(table)

    # Show configuration
    console.print("\n[dim]Configuration:[/dim]")
    console.print(f"  Start date: {start_dt.strftime(DATETIME_FORMAT)}")
    console.print(f"  Max hours/day: {max_hours_per_day}h")
    console.print(f"  Force override: {force}")

    if dry_run:
        console.print("\n[yellow]Note:[/yellow] Changes not saved. Remove --dry-run to apply.")
