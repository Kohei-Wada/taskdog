"""Reopen command - Reopen completed or canceled task(s)."""

import click

from application.dto.reopen_task_request import ReopenTaskRequest
from application.use_cases.reopen_task import ReopenTaskUseCase
from presentation.cli.commands.batch_helpers import execute_batch_operation
from presentation.cli.context import CliContext
from shared.constants import StatusVerbs


@click.command(name="reopen", help="Reopen completed or canceled task(s).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def reopen_command(ctx, task_ids):
    """Reopen completed or canceled task(s).

    Sets task status back to PENDING and clears time tracking.
    Validates that all dependencies are met before reopening.

    Usage:
        taskdog reopen <TASK_ID> [<TASK_ID> ...]

    Examples:
        taskdog reopen 5
        taskdog reopen 3 7 12
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker

    def reopen_single_task(task_id: int) -> None:
        input_dto = ReopenTaskRequest(task_id=task_id)
        use_case = ReopenTaskUseCase(repository, time_tracker)
        task = use_case.execute(input_dto)
        console_writer.task_success(StatusVerbs.REOPENED, task)

    execute_batch_operation(task_ids, reopen_single_task, console_writer, "reopening task")
