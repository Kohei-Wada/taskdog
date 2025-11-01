"""Remove-dependency command - Remove a task dependency."""

import click

from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors


@click.command(name="remove-dependency", help="Remove a dependency from a task.")
@click.argument("task_id", type=int)
@click.argument("depends_on_id", type=int)
@click.pass_context
@handle_task_errors("removing dependency")
def remove_dependency_command(ctx, task_id, depends_on_id):
    """Remove a dependency from a task.

    Usage:
        taskdog remove-dependency <TASK_ID> <DEPENDS_ON_ID>

    Examples:
        taskdog remove-dependency 5 3    # Remove task 3 from task 5's dependencies
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    controller = ctx_obj.task_controller

    task = controller.remove_dependency(task_id, depends_on_id)

    console_writer.success(
        f"Removed dependency: Task {task_id} no longer depends on task {depends_on_id}"
    )
    console_writer.info(f"Task {task_id} dependencies: {task.depends_on}")
