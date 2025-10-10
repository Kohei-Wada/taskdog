"""Remove command - Remove a task."""

import click
from domain.exceptions.task_exceptions import TaskNotFoundException
from utils.console_messages import print_task_not_found_error, print_error
from application.dto.remove_task_input import RemoveTaskInput


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
def remove_command(ctx, task_id, cascade):
    """Remove a task."""
    console = ctx.obj["console"]
    remove_task_use_case = ctx.obj["remove_task_use_case"]

    try:
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

    except TaskNotFoundException as e:
        print_task_not_found_error(console, e.task_id)
    except Exception as e:
        print_error(console, "removing task", e)
