"""`tag list` - List all tags, or the tags of a single task."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from taskdog.cli.error_handler import handle_task_errors

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


@click.command(name="list", help="List all tags, or the tags of a single task.")
@click.argument("task_id", type=int, required=False)
@click.pass_context
@handle_task_errors("listing tags")
def list_command(ctx: click.Context, task_id: int | None) -> None:
    """List tags.

    Usage:
        taskdog tag list        - List all tags with task counts
        taskdog tag list ID     - Show tags for task ID
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    # No argument - show all tags with counts
    if task_id is None:
        stats = ctx_obj.api_client.get_tag_statistics()

        if not stats.tag_counts:
            console_writer.info("No tags found.")
            return

        console_writer.info("All tags:")
        for tag in sorted(stats.tag_counts.keys()):
            count = stats.tag_counts[tag]
            console_writer.print(f"  {tag} ({count} task{'s' if count != 1 else ''})")
        return

    # Task ID - show tags for that task
    result = ctx_obj.api_client.get_task_by_id(task_id)
    if not result.task:
        raise TaskNotFoundException(task_id)

    if not result.task.tags:
        console_writer.info(f"Task {task_id} has no tags.")
    else:
        console_writer.info(f"Tags for task {task_id}:")
        for tag in result.task.tags:
            console_writer.print(f"  {tag}")
