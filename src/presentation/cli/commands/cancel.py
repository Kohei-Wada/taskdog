"""Cancel command - Mark a task as canceled."""

import click

from application.dto.cancel_task_request import CancelTaskRequest
from application.use_cases.cancel_task import CancelTaskUseCase
from presentation.cli.commands.batch_helpers import execute_batch_operation
from presentation.cli.context import CliContext
from shared.constants import StatusVerbs


@click.command(name="cancel", help="Mark task(s) as canceled.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def cancel_command(ctx, task_ids):
    """Mark task(s) as canceled."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    cancel_task_use_case = CancelTaskUseCase(repository, time_tracker)

    def cancel_single_task(task_id: int) -> None:
        input_dto = CancelTaskRequest(task_id=task_id)
        task = cancel_task_use_case.execute(input_dto)

        # Print success message
        console_writer.task_success(StatusVerbs.CANCELED, task)

    execute_batch_operation(task_ids, cancel_single_task, console_writer, "cancel")
