"""Cancel command - Mark a task as canceled."""

import click

from application.dto.cancel_task_input import CancelTaskInput
from application.use_cases.cancel_task import CancelTaskUseCase
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
)
from presentation.cli.context import CliContext


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

    for task_id in task_ids:
        try:
            input_dto = CancelTaskInput(task_id=task_id)
            task = cancel_task_use_case.execute(input_dto)

            # Print success message
            console_writer.task_success("Canceled", task)

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskNotFoundException as e:
            console_writer.validation_error(str(e))
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskAlreadyFinishedError as e:
            console_writer.validation_error(
                f"Cannot cancel task {e.task_id}: Task is already {e.status}. "
                "Task has already finished."
            )
            if len(task_ids) > 1:
                console_writer.empty_line()

        except Exception as e:
            console_writer.error("canceling task", e)
            if len(task_ids) > 1:
                console_writer.empty_line()
