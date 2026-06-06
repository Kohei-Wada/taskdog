"""`tag rm` - Delete a tag from the system."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from taskdog.cli.error_handler import handle_task_errors

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext


@click.command(
    name="rm",
    help="Delete a tag from the system (removes it from all tasks).",
)
@click.argument("tag_name", type=str)
@click.pass_context
@handle_task_errors("deleting tag")
def remove_command(ctx: click.Context, tag_name: str) -> None:
    """Delete a tag from the system, removing it from all tasks.

    Usage:
        taskdog tag rm TAG_NAME
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    delete_result = ctx_obj.api_client.delete_tag(tag_name)
    task_word = "task" if delete_result.affected_task_count == 1 else "tasks"
    console_writer.success(
        f"Deleted tag: {delete_result.tag_name} "
        f"(removed from {delete_result.affected_task_count} {task_word})"
    )
