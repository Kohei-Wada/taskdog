"""Tag command - Delete a tag from the system."""

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors


@click.command(name="tag", help="Manage tags.")
@click.option(
    "-d",
    "--delete",
    "delete_tag_name",
    type=str,
    default=None,
    help="Delete a tag by name (removes from all tasks).",
)
@click.pass_context
@handle_task_errors("managing tag")
def tag_command(
    ctx: click.Context,
    delete_tag_name: str | None,
) -> None:
    """Manage tags.

    Usage:
        taskdog tag -d TAG_NAME  - Delete a tag from the system
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    if delete_tag_name is None:
        console_writer.info("Usage: taskdog tag -d TAG_NAME")
        return

    # Delete tag via API client
    result = ctx_obj.api_client.delete_tag(delete_tag_name)

    task_word = "task" if result.affected_task_count == 1 else "tasks"
    console_writer.success(
        f"Deleted tag: {result.tag_name} "
        f"(removed from {result.affected_task_count} {task_word})"
    )
