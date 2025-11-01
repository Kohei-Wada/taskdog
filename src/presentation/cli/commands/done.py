"""Done command - Mark a task as completed."""

import click

from presentation.cli.commands.batch_helpers import execute_batch_operation
from presentation.cli.context import CliContext
from shared.constants import StatusVerbs


@click.command(name="done", help="Mark task(s) as completed.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def done_command(ctx, task_ids):
    """Mark task(s) as completed."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    controller = ctx_obj.lifecycle_controller

    def complete_single_task(task_id: int) -> None:
        task = controller.complete_task(task_id)

        # Print success message
        console_writer.task_success(StatusVerbs.COMPLETED, task)

        # Show completion details (time, duration, comparison with estimate)
        console_writer.task_completion_details(task)

    execute_batch_operation(task_ids, complete_single_task, console_writer, "complete")
