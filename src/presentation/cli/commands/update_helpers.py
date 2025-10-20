"""Helper functions for update commands to reduce duplication."""

from typing import Any

import click

from application.dto.update_task_request import UpdateTaskRequest
from application.use_cases.update_task import UpdateTaskUseCase
from domain.entities.task import Task
from presentation.cli.context import CliContext


def execute_single_field_update(
    ctx: click.Context,
    task_id: int,
    field_name: str,
    field_value: Any,
) -> Task:
    """Execute a single field update and return updated task.

    This helper reduces code duplication in specialized update commands
    (deadline, priority, estimate, rename).

    Args:
        ctx: Click context containing CliContext
        task_id: ID of task to update
        field_name: Name of field to update (e.g., 'deadline', 'priority')
        field_value: New value for the field

    Returns:
        Updated task

    Raises:
        TaskNotFoundException: If task with given ID does not exist
        TaskValidationError: If update validation fails
    """
    ctx_obj: CliContext = ctx.obj
    update_task_use_case = UpdateTaskUseCase(ctx_obj.repository, ctx_obj.time_tracker)

    # Build DTO with dynamic field
    input_dto = UpdateTaskRequest(task_id=task_id, **{field_name: field_value})

    # Execute use case and return updated task
    task, _ = update_task_use_case.execute(input_dto)
    return task
