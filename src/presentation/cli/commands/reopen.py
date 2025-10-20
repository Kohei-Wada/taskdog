"""Reopen command - Reopen completed or canceled task(s)."""

import click

from application.dto.reopen_task_input import ReopenTaskInput
from application.use_cases.reopen_task import ReopenTaskUseCase
from domain.exceptions.task_exceptions import (
    DependencyNotMetError,
    TaskNotFoundException,
    TaskValidationError,
)
from presentation.cli.context import CliContext


def _reopen_single_task(ctx_obj: CliContext, task_id: int) -> None:
    """Reopen a single task."""
    input_dto = ReopenTaskInput(task_id=task_id)
    use_case = ReopenTaskUseCase(ctx_obj.repository, ctx_obj.time_tracker)
    task = use_case.execute(input_dto)
    ctx_obj.console_writer.task_success("Reopened", task)


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

    for task_id in task_ids:
        try:
            _reopen_single_task(ctx_obj, task_id)
        except TaskNotFoundException as e:
            console_writer.validation_error(str(e))
        except (TaskValidationError, DependencyNotMetError) as e:
            console_writer.validation_error(str(e))
        except Exception as e:
            console_writer.error("reopening task", e)

        # Add spacing between tasks if processing multiple
        if len(task_ids) > 1:
            console_writer.empty_line()
