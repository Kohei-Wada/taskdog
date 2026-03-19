"""Rm command - Remove a task."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext


@click.command(
    name="rm",
    help="Remove task(s) (archive by default, --hard for permanent deletion).",
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.option(
    "--hard",
    is_flag=True,
    help="Permanently delete the task(s) instead of archiving.",
)
@click.pass_context
def rm_command(ctx: click.Context, task_ids: tuple[int, ...], hard: bool) -> None:
    """Remove task(s).

    By default, tasks are archived (is_archived flag set to True) and can be restored with 'taskdog restore'.
    Tasks can be archived from any status (soft delete) while preserving their original status.
    Use --hard flag to permanently delete tasks from the database.
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    if hard:
        results = ctx_obj.api_client.bulk_delete(list(task_ids))
        for result in results.results:
            if result.success:
                console_writer.success(
                    f"Permanently deleted task with ID: {result.task_id}"
                )
            elif result.error is not None:
                console_writer.validation_error(result.error)
            if len(task_ids) > 1:
                console_writer.empty_line()
    else:
        results = ctx_obj.api_client.bulk_archive(list(task_ids))
        for result in results.results:
            if result.success and result.task is not None:
                console_writer.task_success("Archived (status preserved)", result.task)
                console_writer.info(
                    f"Use 'taskdog restore {result.task_id}' to restore this task."
                )
            elif result.error is not None:
                console_writer.validation_error(result.error)
            if len(task_ids) > 1:
                console_writer.empty_line()
