"""Restore command - Restore archived (soft deleted) task(s)."""

import click

from taskdog.cli.commands.batch_helpers import execute_batch_operation
from taskdog.cli.context import CliContext
from taskdog_core.shared.constants import StatusVerbs


@click.command(name="restore", help="Restore archived task(s).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def restore_command(ctx: click.Context, task_ids: tuple[int, ...]) -> None:
    """Restore archived task(s)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    def restore_single_task(task_id: int) -> None:
        # Restore task via API client
        task = ctx_obj.api_client.restore_task(task_id)

        console_writer.task_success(StatusVerbs.RESTORED, task)

    execute_batch_operation(
        task_ids, restore_single_task, console_writer, "restoring task"
    )
