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
            console_writer.print_success("Completed", task)

            # Show completion time and duration if available
            console_writer.print_task_completion_time(task)
            console_writer.print_task_duration(task)

            # Show comparison with estimate if available
            if task.actual_duration_hours and task.estimated_duration:
                console_writer.print_duration_comparison(
                    task.actual_duration_hours, task.estimated_duration
                )

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskNotFoundException as e:
            console_writer.print_validation_error(str(e))
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskAlreadyFinishedError as e:
            console_writer.print_cannot_complete_finished_task_error(e.task_id, str(e.status))
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskNotStartedError as e:
            console_writer.print_cannot_complete_pending_task_error(e.task_id)
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except Exception as e:
            console_writer.print_error("completing task", e)
            if len(task_ids) > 1:
                console_writer.print_empty_line()
