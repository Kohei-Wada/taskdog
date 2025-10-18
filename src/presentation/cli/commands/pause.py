"""Pause command - Pause a task and reset its time tracking."""

import click

from application.dto.pause_task_input import PauseTaskInput
from application.use_cases.pause_task import PauseTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
)
from presentation.cli.context import CliContext


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

    for task_id in task_ids:
        try:
            # Check current status before pausing
            task_before = repository.get_by_id(task_id)
            was_already_pending = task_before and task_before.status == TaskStatus.PENDING

            input_dto = PauseTaskInput(task_id=task_id)
            task = pause_task_use_case.execute(input_dto)

            # Print success message
            if was_already_pending:
                console_writer.info(f"Task {task_id} was already PENDING")
            else:
                console_writer.task_success("Paused", task)
                console_writer.info("Time tracking has been reset")

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskNotFoundException as e:
            console_writer.validation_error(str(e))
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskAlreadyFinishedError as e:
            console_writer.validation_error(
                f"Cannot pause task {e.task_id}: Task is already {e.status}. "
                "Finished tasks cannot be paused."
            )
            if len(task_ids) > 1:
                console_writer.empty_line()

        except Exception as e:
            console_writer.error("pausing task", e)
            if len(task_ids) > 1:
                console_writer.empty_line()
