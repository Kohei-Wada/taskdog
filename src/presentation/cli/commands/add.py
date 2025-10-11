"""Add command - Add a new task."""

import click
from domain.exceptions.task_exceptions import TaskNotFoundException
from shared.click_types.datetime_with_default import DateTimeWithDefault
from utils.console_messages import (
    print_success,
    print_task_not_found_error,
    print_error,
)
from application.dto.create_task_input import CreateTaskInput
from application.use_cases.create_task import CreateTaskUseCase


@click.command(name="add", help="Add a new task with optional planning and deadline.")
@click.argument(
    "parent_id",
    type=int,
    required=False,
)
@click.option(
    "--name",
    prompt="Task name",
    help="The name of the task to add.",
)
@click.option(
    "--priority",
    prompt="Task priority",
    default=1,
)
@click.option(
    "--planned-start",
    type=DateTimeWithDefault(),
    default=None,
    prompt="Planned start",
    prompt_required=False,
    help="Planned start (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, defaults to 18:00:00)",
)
@click.option(
    "--planned-end",
    type=DateTimeWithDefault(),
    default=None,
    prompt="Planned end",
    prompt_required=False,
    help="Planned end (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, defaults to 18:00:00)",
)
@click.option(
    "--deadline",
    type=DateTimeWithDefault(),
    default=None,
    prompt="Task deadline",
    help="Deadline (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, defaults to 18:00:00)",
)
@click.option(
    "--estimated-duration",
    type=float,
    default=None,
    prompt="Estimated duration in hours",
    help="Estimated duration in hours (e.g., 2.5)",
)
@click.pass_context
def add_command(
    ctx,
    name,
    priority,
    parent_id,
    planned_start,
    planned_end,
    deadline,
    estimated_duration,
):
    """Add a new task with optional planning and deadline."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    create_task_use_case = CreateTaskUseCase(repository)

    try:
        # Build input DTO
        input_dto = CreateTaskInput(
            name=name,
            priority=priority,
            parent_id=parent_id,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=estimated_duration,
        )

        # Execute use case
        task = create_task_use_case.execute(input_dto)

        print_success(console, "Added", task)
    except TaskNotFoundException as e:
        print_task_not_found_error(console, e.task_id, is_parent=True)
    except Exception as e:
        print_error(console, "adding task", e)
