"""Helper functions for update commands to reduce duplication."""

from typing import Any

import click

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
    controller = ctx_obj.task_controller

    # Update task via controller with dynamic field
    result = controller.update_task(task_id=task_id, **{field_name: field_value})
    return result.task
