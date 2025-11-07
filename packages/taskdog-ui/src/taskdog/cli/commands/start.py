"""Start command - Start working on a task."""

import click

from taskdog.cli.commands.batch_helpers import execute_batch_operation
from taskdog.cli.context import CliContext
from taskdog_core.shared.constants import StatusVerbs


@click.command(
    name="start", help="Start working on task(s) (sets status to IN_PROGRESS)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def start_command(ctx, task_ids):
    """Start working on tasks (set status to IN_PROGRESS)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    def start_single_task(task_id: int) -> None:
        # Start task via API client
        task = ctx_obj.api_client.start_task(task_id)

        # Print success message
        console_writer.task_success(StatusVerbs.STARTED, task)
        console_writer.task_start_time(task, was_already_in_progress=False)

    execute_batch_operation(task_ids, start_single_task, console_writer, "start")
