"""Task-related converters."""

from typing import Any

from pydantic import BaseModel, ValidationError

from taskdog_core.application.dto.next_tasks_output import NextTasksOutput
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto, TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput

from .exceptions import ConversionError, require_key
from .gantt_converters import convert_to_gantt_overlay


def _model_validate[M: BaseModel](model_cls: type[M], data: dict[str, Any]) -> M:
    """Validate API response data into a DTO, wrapping errors as ConversionError.

    Args:
        model_cls: Pydantic DTO class to build
        data: API response data

    Returns:
        Validated DTO instance

    Raises:
        ConversionError: If the response data cannot be validated into the DTO
    """
    try:
        return model_cls.model_validate(data)
    except ValidationError as e:
        first_error = e.errors()[0]
        field = str(first_error["loc"][0]) if first_error["loc"] else None
        raise ConversionError(
            f"Failed to convert response to {model_cls.__name__}: {e}",
            field=field,
            value=data.get(field) if field else None,
        ) from e


def _build_task_detail_dto(data: dict[str, Any]) -> TaskDetailDto:
    """Build TaskDetailDto from API response data.

    Used by convert_to_get_task_detail_output.

    Args:
        data: API response data containing task fields

    Returns:
        TaskDetailDto with all task data populated

    Raises:
        ConversionError: If the response data cannot be validated into the DTO
    """
    return _model_validate(TaskDetailDto, data)


def convert_to_task_operation_output(data: dict[str, Any]) -> TaskOperationOutput:
    """Convert API response to TaskOperationOutput.

    Args:
        data: API response data

    Returns:
        TaskOperationOutput with task data

    Raises:
        ConversionError: If the response data cannot be validated into the DTO
    """
    return _model_validate(TaskOperationOutput, data)


def convert_to_update_task_output(data: dict[str, Any]) -> TaskUpdateOutput:
    """Convert API response to TaskUpdateOutput.

    Args:
        data: API response data

    Returns:
        TaskUpdateOutput with updated task data and fields
    """
    # Reuse convert_to_task_operation_output to avoid duplication
    task = convert_to_task_operation_output(data)

    # Construct TaskUpdateOutput with nested task and updated_fields
    return TaskUpdateOutput(
        task=task,
        updated_fields=data.get("updated_fields", []),
    )


def convert_to_task_list_output(data: dict[str, Any]) -> TaskListOutput:
    """Convert API response to TaskListOutput.

    Args:
        data: API response data

    Returns:
        TaskListOutput with task list and metadata
    """
    tasks = [_model_validate(TaskRowDto, task) for task in require_key(data, "tasks")]

    # Convert gantt overlay if present (separate reshaping converter)
    gantt_data = None
    if data.get("gantt"):
        gantt_data = convert_to_gantt_overlay(data["gantt"])

    return TaskListOutput(
        tasks=tasks,
        total_count=require_key(data, "total_count"),
        filtered_count=require_key(data, "filtered_count"),
        gantt_data=gantt_data,
    )


def convert_to_next_tasks_output(data: dict[str, Any]) -> NextTasksOutput:
    """Convert API response to NextTasksOutput.

    Args:
        data: API response data

    Returns:
        NextTasksOutput with ranked executable tasks
    """
    tasks = [_model_validate(TaskRowDto, task) for task in require_key(data, "tasks")]
    return NextTasksOutput(
        tasks=tasks, ranking_basis=require_key(data, "ranking_basis")
    )


def convert_to_get_task_detail_output(data: dict[str, Any]) -> TaskDetailOutput:
    """Convert API response to TaskDetailOutput.

    Args:
        data: API response data

    Returns:
        TaskDetailOutput with task data and notes
    """
    # Convert task data using shared method
    task = _build_task_detail_dto(data)

    # Extract notes
    notes_content = data.get("notes")
    has_notes = data.get("has_notes", False)

    return TaskDetailOutput(task=task, notes_content=notes_content, has_notes=has_notes)
