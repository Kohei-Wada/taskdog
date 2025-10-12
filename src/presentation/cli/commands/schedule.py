"""Schedule command - Set planned schedule for a task."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from domain.services.time_tracker import TimeTracker
from presentation.cli.error_handler import handle_task_errors
from shared.click_types.datetime_with_default import DateTimeWithDefault


@click.command(name="schedule", help="Set planned schedule for a task.")
@click.argument("task_id", type=int)
@click.argument("start", type=DateTimeWithDefault())
@click.argument("end", type=DateTimeWithDefault(), required=False)
@click.pass_context
@handle_task_errors("setting schedule")
def schedule_command(ctx, task_id, start, end):
    """Set planned schedule for a task.

    Usage:
        taskdog schedule <TASK_ID> <START> [END]

    Examples:
        taskdog schedule 5 2025-10-15
        taskdog schedule 5 2025-10-15 2025-10-17
        taskdog schedule 5 "2025-10-15 09:00:00" "2025-10-17 18:00:00"
    """
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = TimeTracker()
    update_task_use_case = UpdateTaskUseCase(repository, time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(
        task_id=task_id,
        planned_start=start,
        planned_end=end,
    )

    # Execute use case
    task, updated_fields = update_task_use_case.execute(input_dto)

    # Print success
    console.print(
        f"[green]✓[/green] Set schedule for [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]):"
    )
    if start:
        console.print(f"  Start: [green]{start}[/green]")
    if end:
        console.print(f"  End: [green]{end}[/green]")
