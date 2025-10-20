"""Pause command - Pause a task and reset its time tracking."""

import click

from application.dto.pause_task_input import PauseTaskInput
from application.use_cases.pause_task import PauseTaskUseCase
from domain.entities.task import TaskStatus
from presentation.cli.commands.batch_helpers import execute_batch_operation
from presentation.cli.context import CliContext
from shared.constants import StatusVerbs


@click.command(name="pause", help="Pause task(s) and reset time tracking (sets status to PENDING).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def pause_command(ctx, task_ids):
    """Pause tasks and reset time tracking (set status to PENDING).

    This command is useful when you accidentally started a task and want to reset it.
    It will clear the actual_start and actual_end timestamps.
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    pause_task_use_case = PauseTaskUseCase(repository, time_tracker)

    def pause_single_task(task_id: int) -> None:
        # Check current status before pausing
        task_before = repository.get_by_id(task_id)
        was_already_pending = task_before and task_before.status == TaskStatus.PENDING

        input_dto = PauseTaskInput(task_id=task_id)
        task = pause_task_use_case.execute(input_dto)

        # Print success message
        if was_already_pending:
            console_writer.info(f"Task {task_id} was already PENDING")
        else:
            console_writer.task_success(StatusVerbs.PAUSED, task)
            console_writer.info("Time tracking has been reset")

    execute_batch_operation(task_ids, pause_single_task, console_writer, "pause")
