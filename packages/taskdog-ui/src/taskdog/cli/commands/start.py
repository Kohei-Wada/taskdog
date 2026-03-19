"""Start command - Start working on a task."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext
from taskdog_core.shared.constants import StatusVerbs


@click.command(
    name="start", help="Start working on task(s) (sets status to IN_PROGRESS)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def start_command(ctx: click.Context, task_ids: tuple[int, ...]) -> None:
    """Start working on tasks (set status to IN_PROGRESS)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    results = ctx_obj.api_client.bulk_start(list(task_ids))
    for result in results.results:
        if result.success and result.task is not None:
            console_writer.task_success(StatusVerbs.STARTED, result.task)
            console_writer.task_start_time(result.task, was_already_in_progress=False)
        elif result.error is not None:
            console_writer.validation_error(result.error)
        if len(task_ids) > 1:
            console_writer.empty_line()
