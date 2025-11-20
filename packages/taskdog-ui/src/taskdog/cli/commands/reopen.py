"""Reopen command - Reopen completed or canceled task(s)."""

import click

from taskdog.cli.commands.batch_helpers import execute_batch_operation
from taskdog.cli.context import CliContext
from taskdog_core.shared.constants import StatusVerbs


@click.command(name="reopen", help="Reopen completed or canceled task(s).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def reopen_command(ctx: click.Context, task_ids: tuple[int, ...]) -> None:
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

    def reopen_single_task(task_id: int) -> None:
        # Reopen task via API client
        task = ctx_obj.api_client.reopen_task(task_id)

        console_writer.task_success(StatusVerbs.REOPENED, task)

    execute_batch_operation(
        task_ids, reopen_single_task, console_writer, "reopening task"
    )
