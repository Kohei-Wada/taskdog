"""Add command - Add a new task."""

import click

from application.dto.create_task_input import CreateTaskInput
from application.use_cases.create_task import CreateTaskUseCase
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
@click.pass_context
@handle_task_errors("adding task", is_parent=True)
def add_command(ctx, name, priority):
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
    )

    # Execute use case
    task = create_task_use_case.execute(input_dto)

    console_writer.success("Added", task)
