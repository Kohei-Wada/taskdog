"""Rm command - Remove a task."""

import click

from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from presentation.cli.batch_executor import BatchCommandExecutor
from presentation.cli.context import CliContext


@click.command(name="rm", help="Remove task(s) permanently (use archive to preserve data).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.option(
    "--cascade",
    is_flag=True,
    help="Delete all child tasks recursively.",
)
@click.pass_context
def rm_command(ctx, task_ids, cascade):
    """Remove task(s)."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    remove_task_use_case = RemoveTaskUseCase(repository)

    # Track total removed for summary
    total_removed = [0]  # Use list to allow modification in closure

    # Define processing function
    def process_task(task_id: int):
        input_dto = RemoveTaskInput(task_id=task_id, cascade=cascade)
        removed_count = remove_task_use_case.execute(input_dto)
        total_removed[0] += removed_count
        return (task_id, removed_count)

    # Define success callback
    def on_success(result):
        task_id, removed_count = result
        if cascade:
            console.print(
                f"[green]✓[/green] Removed task [cyan]{task_id}[/cyan] and [bold]{
                    removed_count - 1
                }[/bold] child task(s)"
            )
        else:
            console.print(f"[green]✓[/green] Removed task with ID: [cyan]{task_id}[/cyan]")

    # Execute batch operation
    executor = BatchCommandExecutor(console)
    success_count, error_count, _ = executor.execute_batch(
        task_ids=task_ids,
        process_func=process_task,
        operation_name="removing task",
        success_callback=on_success,
        show_summary=False,  # Use custom summary with total_removed count
    )

    # Show custom summary with total_removed count
    if len(task_ids) > 1:
        if success_count > 0 and error_count == 0:
            console.print(f"[green]✓[/green] Successfully removed {total_removed[0]} task(s)")
        elif success_count > 0 and error_count > 0:
            console.print(
                f"[yellow]⚠[/yellow] Removed {total_removed[0]} task(s), {error_count} error(s)"
            )
        elif error_count > 0:
            console.print(f"[red]✗[/red] Failed to remove {error_count} task(s)")
