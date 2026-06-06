"""`tag set` - Set (replace) the tags of a task."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from taskdog.cli.error_handler import handle_task_errors

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext


@click.command(name="set", help="Set (replace) the tags of a task.")
@click.argument("task_id", type=int)
@click.argument("tags", nargs=-1)
@click.pass_context
@handle_task_errors("setting tags")
def set_command(ctx: click.Context, task_id: int, tags: tuple[str, ...]) -> None:
    """Set the tags of a task, replacing any existing tags.

    Usage:
        taskdog tag set ID tag1 tag2  - Replace task ID's tags
        taskdog tag set ID            - Clear all tags from task ID
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    updated_task = ctx_obj.api_client.set_task_tags(task_id, list(tags))

    if updated_task.tags:
        console_writer.task_success("Set tags for", updated_task)
        console_writer.print(f"  Tags: {', '.join(updated_task.tags)}")
    else:
        console_writer.task_success("Cleared tags for", updated_task)
