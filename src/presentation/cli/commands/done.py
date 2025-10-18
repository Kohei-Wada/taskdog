"""Done command - Mark a task as completed."""

import click

from application.dto.complete_task_input import CompleteTaskInput
from application.use_cases.complete_task import CompleteTaskUseCase
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
)
from presentation.cli.context import CliContext


@click.command(name="done", help="Mark task(s) as completed.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def done_command(ctx, task_ids):  # noqa: C901
    """Mark task(s) as completed."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    complete_task_use_case = CompleteTaskUseCase(repository, time_tracker)

    for task_id in task_ids:
        try:
            input_dto = CompleteTaskInput(task_id=task_id)
            task = complete_task_use_case.execute(input_dto)

            # Print success message
            console_writer.task_success("Completed", task)

            # Show completion details (time, duration, comparison with estimate)
            console_writer.task_completion_details(task)

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskNotFoundException as e:
            console_writer.validation_error(str(e))
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskAlreadyFinishedError as e:
            console_writer.validation_error(
                f"Cannot complete task {e.task_id}: Task is already {e.status}. "
                "Task has already been completed."
            )
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskNotStartedError as e:
            console_writer.validation_error(
                f"Cannot complete task {e.task_id}: Task is still PENDING. "
                f"Start the task first with: taskdog start {e.task_id}"
            )
            if len(task_ids) > 1:
                console_writer.empty_line()

        except Exception as e:
            console_writer.error("completing task", e)
            if len(task_ids) > 1:
                console_writer.empty_line()
