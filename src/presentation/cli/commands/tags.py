"""Tags command - Manage task tags."""

import click

from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors


@click.command(name="tags", help="View or set task tags.")
@click.argument("task_id", type=int, required=False)
@click.argument("tags", nargs=-1)
@click.pass_context
@handle_task_errors("managing tags")
def tags_command(ctx, task_id, tags):
    """View or set task tags.

    Usage:
        taskdog tags           - List all tags with task counts
        taskdog tags ID        - Show tags for task ID
        taskdog tags ID tag1 tag2  - Set tags for task ID (replaces existing tags)
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

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
        # Get task via API client
        task = ctx_obj.api_client.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundException(task_id)

        if not task.tags:
            console_writer.info(f"Task {task_id} has no tags.")
        else:
            console_writer.info(f"Tags for task {task_id}:")
            for tag in task.tags:
                console_writer.print(f"  {tag}")
        return

    # Case 3: Task ID + tags - set tags
    # Set tags via API client
    task = ctx_obj.api_client.set_task_tags(task_id, list(tags))

    if task.tags:
        console_writer.task_success("Set tags for", task)
        console_writer.print(f"  Tags: {', '.join(task.tags)}")
    else:
        console_writer.task_success("Cleared tags for", task)
