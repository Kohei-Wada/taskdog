"""Archive command - Archive a task."""

import click

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.archive_task import ArchiveTaskUseCase
from presentation.cli.batch_executor import BatchCommandExecutor
from presentation.cli.context import CliContext


@click.command(
    name="archive", help="Archive task(s) for data retention (hidden from views by default)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def archive_command(ctx, task_ids):
    """Archive task(s)."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    archive_task_use_case = ArchiveTaskUseCase(repository)

    # Define processing function
    def process_task(task_id: int):
        input_dto = ArchiveTaskInput(task_id=task_id)
        archive_task_use_case.execute(input_dto)
        return task_id

    # Define success callback
    def on_success(result):
        task_id = result
        console.print(f"[green]✓[/green] Archived task with ID: [cyan]{task_id}[/cyan]")

    # Execute batch operation
    executor = BatchCommandExecutor(console)
    executor.execute_batch(
        task_ids=task_ids,
        process_func=process_task,
        operation_name="archiving task",
        success_callback=on_success,
    )
