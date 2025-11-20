"""Cancel command - Mark a task as canceled."""

import click

from taskdog.cli.commands.batch_helpers import execute_batch_operation
from taskdog.cli.context import CliContext
from taskdog_core.shared.constants import StatusVerbs


@click.command(name="cancel", help="Mark task(s) as canceled.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def cancel_command(ctx: click.Context, task_ids: tuple[int, ...]) -> None:
    """Mark task(s) as canceled."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    def cancel_single_task(task_id: int) -> None:
        # Cancel task via API client
        task = ctx_obj.api_client.cancel_task(task_id)

        # Print success message
        console_writer.task_success(StatusVerbs.CANCELED, task)

    execute_batch_operation(task_ids, cancel_single_task, console_writer, "cancel")
