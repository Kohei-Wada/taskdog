"""Reopen command - Reopen completed or canceled task(s)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
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

    results = ctx_obj.api_client.bulk_reopen(list(task_ids))
    for result in results.results:
        if result.success and result.task is not None:
            console_writer.task_success(StatusVerbs.REOPENED, result.task)
        elif result.error is not None:
            console_writer.validation_error(result.error)
        if len(task_ids) > 1:
            console_writer.empty_line()
