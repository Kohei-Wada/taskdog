"""Rename command - Rename a task."""

import click
from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from domain.services.time_tracker import TimeTracker
from presentation.cli.error_handler import handle_task_errors


@click.command(name="rename", help="Rename a task.")
@click.argument("task_id", type=int)
@click.argument("name", type=str)
@click.pass_context
@handle_task_errors("renaming task")
def rename_command(ctx, task_id, name):
    """Rename a task.

    Usage:
        taskdog rename <TASK_ID> <NEW_NAME>

    Examples:
        taskdog rename 5 "Implement authentication"
        taskdog rename 10 "Fix bug in login form"
    """
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = TimeTracker()
    update_task_use_case = UpdateTaskUseCase(repository, time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(task_id=task_id, name=name)

    # Execute use case
    task, _ = update_task_use_case.execute(input_dto)

    # Print success
    console.print(
        f"[green]✓[/green] Renamed task (ID: [cyan]{task.id}[/cyan]): [bold]{name}[/bold]"
    )
