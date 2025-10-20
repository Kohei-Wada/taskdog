"""Restore command - Restore archived (soft deleted) task(s)."""

import click

from application.dto.restore_task_request import RestoreTaskRequest
from application.use_cases.restore_task import RestoreTaskUseCase
from presentation.cli.commands.batch_helpers import execute_batch_operation
from presentation.cli.context import CliContext
from shared.constants import StatusVerbs


@click.command(name="restore", help="Restore archived task(s).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def restore_command(ctx, task_ids):
    """Restore archived task(s)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository

    def restore_single_task(task_id: int) -> None:
        input_dto = RestoreTaskRequest(task_id=task_id)
        use_case = RestoreTaskUseCase(repository)
        task = use_case.execute(input_dto)
        console_writer.task_success(StatusVerbs.RESTORED, task)

    execute_batch_operation(task_ids, restore_single_task, console_writer, "restoring task")
