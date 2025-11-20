"""Pause command - Pause a task and reset its time tracking."""

import click

from taskdog.cli.commands.batch_helpers import execute_batch_operation
from taskdog.cli.context import CliContext
from taskdog_core.shared.constants import StatusVerbs


@click.command(
    name="pause", help="Pause task(s) and reset time tracking (sets status to PENDING)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def pause_command(ctx: click.Context, task_ids: tuple[int, ...]) -> None:
    """Pause tasks and reset time tracking (set status to PENDING).

    This command is useful when you accidentally started a task and want to reset it.
    It will clear the actual_start and actual_end timestamps.
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    def pause_single_task(task_id: int) -> None:
        # Pause task via API client
        task = ctx_obj.api_client.pause_task(task_id)

        # Print success message
        console_writer.task_success(StatusVerbs.PAUSED, task)
        console_writer.info("Time tracking has been reset")

    execute_batch_operation(task_ids, pause_single_task, console_writer, "pause")
