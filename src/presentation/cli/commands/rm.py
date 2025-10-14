"""Rm command - Remove a task."""

import click

from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from presentation.cli.batch_executor import BatchCommandExecutor
from presentation.cli.context import CliContext


@click.command(name="rm", help="Remove task(s) permanently (use archive to preserve data).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def rm_command(ctx, task_ids):
    """Remove task(s)."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    remove_task_use_case = RemoveTaskUseCase(repository)

    # Define processing function
    def process_task(task_id: int):
        input_dto = RemoveTaskInput(task_id=task_id)
        remove_task_use_case.execute(input_dto)
        return task_id

    # Define success callback
    def on_success(result):
        task_id = result
        console.print(f"[green]✓[/green] Removed task with ID: [cyan]{task_id}[/cyan]")

    # Execute batch operation
    executor = BatchCommandExecutor(console)
    executor.execute_batch(
        task_ids=task_ids,
        process_func=process_task,
        operation_name="removing task",
        success_callback=on_success,
    )
