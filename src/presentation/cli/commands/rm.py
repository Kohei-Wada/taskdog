"""Rm command - Remove a task."""

import click
from domain.exceptions.task_exceptions import TaskNotFoundException
from utils.console_messages import print_task_not_found_error, print_error
from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase


@click.command(
    name="rm", help="Remove task(s) (orphan children by default, or cascade delete)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.option(
    "--cascade",
    is_flag=True,
    help="Delete all child tasks recursively.",
)
@click.pass_context
def rm_command(ctx, task_ids, cascade):
    """Remove task(s)."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    remove_task_use_case = RemoveTaskUseCase(repository)

    success_count = 0
    error_count = 0
    total_removed = 0

    for task_id in task_ids:
        try:
            input_dto = RemoveTaskInput(task_id=task_id, cascade=cascade)
            removed_count = remove_task_use_case.execute(input_dto)
            total_removed += removed_count

            if cascade:
                console.print(
                    f"[green]✓[/green] Removed task [cyan]{task_id}[/cyan] and [bold]{removed_count - 1}[/bold] child task(s)"
                )
            else:
                console.print(
                    f"[green]✓[/green] Removed task with ID: [cyan]{task_id}[/cyan]"
                )

            success_count += 1

            # Add spacing between multiple tasks
            if len(task_ids) > 1:
                console.print()

        except TaskNotFoundException as e:
            print_task_not_found_error(console, e.task_id)
            error_count += 1
            if len(task_ids) > 1:
                console.print()
        except Exception as e:
            print_error(console, "removing task", e)
            error_count += 1
            if len(task_ids) > 1:
                console.print()

    # Show summary if multiple tasks were processed
    if len(task_ids) > 1:
        if success_count > 0 and error_count == 0:
            console.print(f"[green]✓[/green] Successfully removed {total_removed} task(s)")
        elif success_count > 0 and error_count > 0:
            console.print(f"[yellow]⚠[/yellow] Removed {total_removed} task(s), {error_count} error(s)")
        elif error_count > 0:
            console.print(f"[red]✗[/red] Failed to remove {error_count} task(s)")
