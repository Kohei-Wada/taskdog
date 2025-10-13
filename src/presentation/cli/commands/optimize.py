"""Optimize command - Auto-generate optimal task schedules."""

from datetime import datetime

import click

from application.services.optimization_summary_builder import OptimizationSummaryBuilder
from application.use_cases.optimize_schedule import OptimizeScheduleInput, OptimizeScheduleUseCase
from domain.constants import DATETIME_FORMAT, DEFAULT_START_HOUR
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
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
    type=float,
    default=6.0,
    help="Max work hours per day (default: 6.0)",
)
@click.option("--force", "-f", is_flag=True, help="Override existing schedules")
@click.option("--dry-run", is_flag=True, help="Preview without saving")
@click.pass_context
@handle_command_errors("optimizing schedules")
def optimize_command(ctx, start_date, max_hours_per_day, force, dry_run):
    """Auto-generate optimal schedules for tasks."""
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
