"""Pause command - Pause a task and reset its time tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
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

    results = ctx_obj.api_client.bulk_pause(list(task_ids))
    for result in results.results:
        if result.success and result.task is not None:
            console_writer.task_success(StatusVerbs.PAUSED, result.task)
            console_writer.info("Time tracking has been reset")
        elif result.error is not None:
            console_writer.validation_error(result.error)
        if len(task_ids) > 1:
            console_writer.empty_line()
