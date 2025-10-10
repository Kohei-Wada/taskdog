"""Estimate command - Set estimated duration for a task."""

import click
from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from domain.services.time_tracker import TimeTracker
from presentation.cli.error_handler import handle_task_errors


@click.command(name="estimate", help="Set estimated duration for a task.")
@click.argument("task_id", type=int)
@click.argument("hours", type=float)
@click.pass_context
@handle_task_errors("setting estimate")
def estimate_command(ctx, task_id, hours):
    """Set estimated duration for a task.

    Usage:
        taskdog estimate <TASK_ID> <HOURS>

    Examples:
        taskdog estimate 5 2.5
        taskdog estimate 10 8.0
    """
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = TimeTracker()
    update_task_use_case = UpdateTaskUseCase(repository, time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(task_id=task_id, estimated_duration=hours)

    # Execute use case
    task, _ = update_task_use_case.execute(input_dto)

    # Print success
    console.print(
        f"[green]✓[/green] Set estimate for [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]): [yellow]{hours}h[/yellow]"
    )
