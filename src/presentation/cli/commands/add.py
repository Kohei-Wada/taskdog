"""Add command - Add a new task."""

import click

from domain.exceptions.task_exceptions import TaskValidationError
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors


@click.command(name="add", help="Add a new task.")
@click.argument("name", type=str)
@click.option(
    "--priority",
    "-p",
    type=int,
    default=None,
    help="Task priority (default: from config or 5, higher value = higher priority)",
)
@click.option(
    "--fixed",
    "-f",
    is_flag=True,
    help="Mark task as fixed (won't be rescheduled by optimizer)",
)
@click.option(
    "--depends-on",
    "-d",
    multiple=True,
    type=int,
    help="Task IDs this task depends on (can be specified multiple times)",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    type=str,
    help="Tags for categorization and filtering (can be specified multiple times)",
)
@click.pass_context
@handle_task_errors("adding task", is_parent=True)
def add_command(ctx, name, priority, fixed, depends_on, tag):
    """Add a new task.

    Usage:
        taskdog add "Task name"
        taskdog add "Task name" --priority 3
        taskdog add "Task name" -p 2

    To set deadline, estimate, or schedule, use dedicated commands after creation:
        taskdog deadline <ID> <DATE>
        taskdog estimate <ID> <HOURS>
        taskdog schedule <ID> <START> [END]

    Examples:
        taskdog add "Implement authentication"
        taskdog add "Fix login bug" -p 5
        taskdog add "Add unit tests"
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    crud_controller = ctx_obj.crud_controller
    relationship_controller = ctx_obj.relationship_controller

    # Create task via controller
    task = crud_controller.create_task(
        name=name,
        priority=priority,  # Controller handles default priority
        is_fixed=fixed,
        tags=list(tag) if tag else None,
    )

    # Add dependencies if specified
    if depends_on:
        for dep_id in depends_on:
            try:
                task = relationship_controller.add_dependency(task.id, dep_id)
            except TaskValidationError as e:
                console_writer.validation_error(str(e))
                # Continue adding other dependencies even if one fails

    console_writer.task_success("Added", task)
    if task.depends_on:
        console_writer.info(f"Dependencies: {task.depends_on}")
    if task.tags:
        console_writer.info(f"Tags: {', '.join(task.tags)}")
