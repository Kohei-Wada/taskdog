"""Archive command - Archive a task."""

import click

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.archive_task import ArchiveTaskUseCase
from presentation.cli.batch_executor import BatchCommandExecutor


@click.command(
    name="archive", help="Archive task(s) (orphan children by default, or cascade archive)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.option(
    "--cascade",
    is_flag=True,
    help="Archive all child tasks recursively.",
)
@click.pass_context
def archive_command(ctx, task_ids, cascade):
    """Archive task(s)."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    archive_task_use_case = ArchiveTaskUseCase(repository)

    # Track total archived for summary
    total_archived = [0]  # Use list to allow modification in closure

    # Define processing function
    def process_task(task_id: int):
        input_dto = ArchiveTaskInput(task_id=task_id, cascade=cascade)
        archived_count = archive_task_use_case.execute(input_dto)
        total_archived[0] += archived_count
        return (task_id, archived_count)

    # Define success callback
    def on_success(result):
        task_id, archived_count = result
        if cascade:
            console.print(
                f"[green]✓[/green] Archived task [cyan]{task_id}[/cyan] and [bold]{archived_count - 1}[/bold] child task(s)"
            )
        else:
            console.print(f"[green]✓[/green] Archived task with ID: [cyan]{task_id}[/cyan]")

    # Execute batch operation
    executor = BatchCommandExecutor(console)
    success_count, error_count, _ = executor.execute_batch(
        task_ids=task_ids,
        process_func=process_task,
        operation_name="archiving task",
        success_callback=on_success,
        show_summary=False,  # Use custom summary with total_archived count
    )

    # Show custom summary with total_archived count
    if len(task_ids) > 1:
        if success_count > 0 and error_count == 0:
            console.print(f"[green]✓[/green] Successfully archived {total_archived[0]} task(s)")
        elif success_count > 0 and error_count > 0:
            console.print(
                f"[yellow]⚠[/yellow] Archived {total_archived[0]} task(s), {error_count} error(s)"
            )
        elif error_count > 0:
            console.print(f"[red]✗[/red] Failed to archive {error_count} task(s)")
