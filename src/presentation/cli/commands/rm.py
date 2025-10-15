"""Rm command - Remove a task."""

import click

from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.context import CliContext
from utils.console_messages import print_error, print_task_not_found_error


@click.command(name="rm", help="Remove task(s) permanently (use archive to preserve data).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def rm_command(ctx, task_ids):
    """Remove task(s)."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    remove_task_use_case = RemoveTaskUseCase(repository)

    for task_id in task_ids:
        try:
            input_dto = RemoveTaskInput(task_id=task_id)
            remove_task_use_case.execute(input_dto)

            console.print(f"[green]✓[/green] Removed task with ID: [cyan]{task_id}[/cyan]")

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console.print()

        except TaskNotFoundException as e:
            print_task_not_found_error(console, e.task_id)
            if len(task_ids) > 1:
                console.print()

        except Exception as e:
            print_error(console, "removing task", e)
            if len(task_ids) > 1:
                console.print()
