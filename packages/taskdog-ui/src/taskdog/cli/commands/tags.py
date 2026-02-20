"""Tags command - Manage task tags."""

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


@click.command(name="tags", help="View, set, or delete task tags.")
@click.argument("task_id", type=int, required=False)
@click.argument("tags", nargs=-1)
@click.option(
    "-d",
    "--delete",
    "delete_tag_name",
    type=str,
    default=None,
    help="Delete a tag by name (removes from all tasks).",
)
@click.pass_context
@handle_task_errors("managing tags")
def tags_command(
    ctx: click.Context,
    task_id: int | None,
    tags: tuple[str, ...],
    delete_tag_name: str | None,
) -> None:
    """View, set, or delete task tags.

    Usage:
        taskdog tags              - List all tags with task counts
        taskdog tags ID           - Show tags for task ID
        taskdog tags ID tag1 tag2 - Set tags for task ID (replaces existing tags)
        taskdog tags -d TAG_NAME  - Delete a tag from the system
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    # Delete tag mode
    if delete_tag_name is not None:
        delete_result = ctx_obj.api_client.delete_tag(delete_tag_name)
        task_word = "task" if delete_result.affected_task_count == 1 else "tasks"
        console_writer.success(
            f"Deleted tag: {delete_result.tag_name} "
            f"(removed from {delete_result.affected_task_count} {task_word})"
        )
        return

    # Case 1: No arguments - show all tags
    if task_id is None:
        # Query tag statistics via API client
        stats = ctx_obj.api_client.get_tag_statistics()

        if not stats.tag_counts:
            console_writer.info("No tags found.")
            return

        console_writer.info("All tags:")
        # Sort by tag name
        for tag in sorted(stats.tag_counts.keys()):
            count = stats.tag_counts[tag]
            console_writer.print(f"  {tag} ({count} task{'s' if count != 1 else ''})")
        return

    # Case 2: Task ID only - show tags for that task
    if not tags:
        # Get task via API client (returns TaskByIdOutput with nested TaskDetailDto)
        result = ctx_obj.api_client.get_task_by_id(task_id)
        if not result.task:
            raise TaskNotFoundException(task_id)

        if not result.task.tags:
            console_writer.info(f"Task {task_id} has no tags.")
        else:
            console_writer.info(f"Tags for task {task_id}:")
            for tag in result.task.tags:
                console_writer.print(f"  {tag}")
        return

    # Case 3: Task ID + tags - set tags
    # Set tags via API client (returns TaskOperationOutput)
    updated_task = ctx_obj.api_client.set_task_tags(task_id, list(tags))

    if updated_task.tags:
        console_writer.task_success("Set tags for", updated_task)
        console_writer.print(f"  Tags: {', '.join(updated_task.tags)}")
    else:
        console_writer.task_success("Cleared tags for", updated_task)
