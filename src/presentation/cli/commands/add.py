"""Add command - Add a new task."""

import click

from application.dto.create_task_input import CreateTaskInput
from application.dto.manage_dependencies_input import AddDependencyInput
from application.use_cases.add_dependency import AddDependencyUseCase
from application.use_cases.create_task import CreateTaskUseCase
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
@click.pass_context
@handle_task_errors("adding task", is_parent=True)
def add_command(ctx, name, priority, fixed, depends_on):
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
    repository = ctx_obj.repository
    config = ctx_obj.config
    create_task_use_case = CreateTaskUseCase(repository)

    # Use config default if priority not specified
    effective_priority = priority if priority is not None else config.task.default_priority

    # Build input DTO (only basic fields)
    input_dto = CreateTaskInput(
        name=name,
        priority=effective_priority,
        is_fixed=fixed,
    )

    # Execute use case
    task = create_task_use_case.execute(input_dto)

    # Add dependencies if specified
    if depends_on:
        add_dep_use_case = AddDependencyUseCase(repository)
        for dep_id in depends_on:
            try:
                dep_input = AddDependencyInput(task_id=task.id, depends_on_id=dep_id)
                task = add_dep_use_case.execute(dep_input)
            except TaskValidationError as e:
                console_writer.validation_error(str(e))
                # Continue adding other dependencies even if one fails

    console_writer.task_success("Added", task)
    if task.depends_on:
        console_writer.info(f"Dependencies: {task.depends_on}")
