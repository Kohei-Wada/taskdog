"""Rm command - Remove a task."""

import click

from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.context import CliContext


@click.command(name="rm", help="Remove task(s) permanently (use archive to preserve data).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def rm_command(ctx, task_ids):
    """Remove task(s)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    remove_task_use_case = RemoveTaskUseCase(repository)

    for task_id in task_ids:
        try:
            input_dto = RemoveTaskInput(task_id=task_id)
            remove_task_use_case.execute(input_dto)

            console_writer.print_task_removed(task_id)

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskNotFoundException as e:
            console_writer.print_task_not_found_error(e.task_id)
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except Exception as e:
            console_writer.print_error("removing task", e)
            if len(task_ids) > 1:
                console_writer.print_empty_line()
