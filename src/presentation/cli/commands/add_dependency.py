"""Add-dependency command - Add a task dependency."""

import click

from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors


@click.command(name="add-dependency", help="Add a dependency to a task.")
@click.argument("task_id", type=int)
@click.argument("depends_on_id", type=int)
@click.pass_context
@handle_task_errors("adding dependency")
def add_dependency_command(ctx, task_id, depends_on_id):
    """Add a dependency to a task.

    Usage:
        taskdog add-dependency <TASK_ID> <DEPENDS_ON_ID>

    Examples:
        taskdog add-dependency 5 3    # Task 5 depends on task 3
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    controller = ctx_obj.relationship_controller

    task = controller.add_dependency(task_id, depends_on_id)

    console_writer.success(f"Added dependency: Task {task_id} now depends on task {depends_on_id}")
    console_writer.info(f"Task {task_id} dependencies: {task.depends_on}")
