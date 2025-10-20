"""Restore command - Restore archived (soft deleted) task(s)."""

import click

from application.dto.restore_task_input import RestoreTaskInput
from application.use_cases.restore_task import RestoreTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.context import CliContext


@click.command(name="restore", help="Restore archived task(s).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def restore_command(ctx, task_ids):
    """Restore archived task(s)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    restore_task_use_case = RestoreTaskUseCase(repository)

    for task_id in task_ids:
        try:
            input_dto = RestoreTaskInput(task_id=task_id)
            task = restore_task_use_case.execute(input_dto)

            # Print success message
            console_writer.task_success("Restored", task)

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskNotFoundException as e:
            console_writer.validation_error(str(e))
            if len(task_ids) > 1:
                console_writer.empty_line()

        except Exception as e:
            console_writer.error("restoring task", e)
            if len(task_ids) > 1:
                console_writer.empty_line()
