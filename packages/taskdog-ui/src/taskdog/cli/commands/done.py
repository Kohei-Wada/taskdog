"""Done command - Mark a task as completed."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext
from taskdog_core.shared.constants import StatusVerbs


@click.command(name="done", help="Mark task(s) as completed.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def done_command(ctx: click.Context, task_ids: tuple[int, ...]) -> None:
    """Mark task(s) as completed."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    results = ctx_obj.api_client.bulk_complete(list(task_ids))
    for result in results.results:
        if result.success and result.task is not None:
            console_writer.task_success(StatusVerbs.COMPLETED, result.task)
            console_writer.task_completion_details(result.task)
        elif result.error is not None:
            console_writer.validation_error(result.error)
        if len(task_ids) > 1:
            console_writer.empty_line()
