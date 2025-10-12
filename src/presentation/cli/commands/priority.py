"""Priority command - Set task priority."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.cli.error_handler import handle_task_errors


@click.command(name="priority", help="Set task priority.")
@click.argument("task_id", type=int)
@click.argument("priority", type=int)
@click.pass_context
@handle_task_errors("setting priority")
def priority_command(ctx, task_id, priority):
    """Set priority for a task.

    Usage:
        taskdog priority <TASK_ID> <PRIORITY>

    Examples:
        taskdog priority 5 3
        taskdog priority 10 1
    """
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = ctx.obj["time_tracker"]
    update_task_use_case = UpdateTaskUseCase(repository, time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(task_id=task_id, priority=priority)

    # Execute use case
    task, _ = update_task_use_case.execute(input_dto)

    # Print success
    console.print(
        f"[green]✓[/green] Set priority for [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]): [yellow]{priority}[/yellow]"
    )
