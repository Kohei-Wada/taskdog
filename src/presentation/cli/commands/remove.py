"""Remove command - Remove a task."""

import click
from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from presentation.cli.error_handler import handle_task_errors


@click.command(
    name="remove", help="Remove a task (orphan children by default, or cascade delete)."
)
@click.argument("task_id", type=int)
@click.option(
    "--cascade",
    is_flag=True,
    help="Delete all child tasks recursively.",
)
@click.pass_context
@handle_task_errors("removing task")
def remove_command(ctx, task_id, cascade):
    """Remove a task."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    remove_task_use_case = RemoveTaskUseCase(repository)

    input_dto = RemoveTaskInput(task_id=task_id, cascade=cascade)
    removed_count = remove_task_use_case.execute(input_dto)

    if cascade:
        console.print(
            f"[green]✓[/green] Removed [bold]{removed_count}[/bold] task(s) (including children)"
        )
    else:
        console.print(
            f"[green]✓[/green] Removed task with ID: [cyan]{task_id}[/cyan]"
        )
