"""Task-related converters."""

from typing import Any

from taskdog_core.application.dto.get_task_by_id_output import TaskByIdOutput
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto, TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.domain.entities.task import TaskStatus

from .datetime_utils import (
    _parse_date_dict,
    _parse_datetime_fields,
    _parse_required_datetime,
)
from .gantt_converters import convert_to_gantt_output


def _build_task_detail_dto(data: dict[str, Any]) -> TaskDetailDto:
    """Build TaskDetailDto from API response data.

    This is a shared method to avoid duplication between convert_to_get_task_by_id_output
    and convert_to_get_task_detail_output.

    Args:
        data: API response data containing task fields

    Returns:
        TaskDetailDto with all task data populated
    """
    # Parse datetime fields with error handling
    dt_fields = _parse_datetime_fields(
        data, ["planned_start", "planned_end", "deadline", "actual_start", "actual_end"]
    )

    # Build and return TaskDetailDto with safe parsing
    return TaskDetailDto(
        id=data["id"],
        name=data["name"],
        priority=data["priority"],
        status=TaskStatus(data["status"]),
        planned_start=dt_fields["planned_start"],
        planned_end=dt_fields["planned_end"],
        deadline=dt_fields["deadline"],
        actual_start=dt_fields["actual_start"],
        actual_end=dt_fields["actual_end"],
        estimated_duration=data.get("estimated_duration"),
        daily_allocations=_parse_date_dict(data, "daily_allocations"),
        is_fixed=data.get("is_fixed", False),
        depends_on=data.get("depends_on", []),
        actual_daily_hours=_parse_date_dict(data, "actual_daily_hours"),
        tags=data.get("tags", []),
        is_archived=data.get("is_archived", False),
        created_at=_parse_required_datetime(data, "created_at"),
        updated_at=_parse_required_datetime(data, "updated_at"),
        actual_duration_hours=data.get("actual_duration_hours"),
        is_active=data.get("is_active", False),
        is_finished=data.get("is_finished", False),
        can_be_modified=data.get("can_be_modified", False),
        is_schedulable=data.get("is_schedulable", False),
    )


def convert_to_task_operation_output(data: dict[str, Any]) -> TaskOperationOutput:
    """Convert API response to TaskOperationOutput.

    Args:
        data: API response data

    Returns:
        TaskOperationOutput with task data
    """
    # Parse datetime fields using utility
    dt_fields = _parse_datetime_fields(
        data, ["deadline", "planned_start", "planned_end", "actual_start", "actual_end"]
    )

    return TaskOperationOutput(
        id=data["id"],
        name=data["name"],
        status=TaskStatus(data["status"]),
        priority=data["priority"],
        deadline=dt_fields["deadline"],
        estimated_duration=data.get("estimated_duration"),
        planned_start=dt_fields["planned_start"],
        planned_end=dt_fields["planned_end"],
        actual_start=dt_fields["actual_start"],
        actual_end=dt_fields["actual_end"],
        depends_on=data.get("depends_on", []),
        tags=data.get("tags", []),
        is_fixed=data.get("is_fixed", False),
        is_archived=data.get("is_archived", False),
        actual_duration_hours=data.get("actual_duration_hours"),
        actual_daily_hours=data.get("actual_daily_hours", {}),
        daily_allocations=data.get("daily_allocations", {}),
    )


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


def convert_to_task_list_output(
    data: dict[str, Any], has_notes_cache: dict[int, bool] | None = None
) -> TaskListOutput:
    """Convert API response to TaskListOutput.

    Args:
        data: API response data
        has_notes_cache: Optional cache dictionary to populate with has_notes info

    Returns:
        TaskListOutput with task list and metadata
    """
    tasks = []
    for task in data["tasks"]:
        # Cache has_notes information if cache provided
        if has_notes_cache is not None:
            has_notes_cache[task["id"]] = task.get("has_notes", False)

        # Parse datetime fields using utility
        dt_fields = _parse_datetime_fields(
            task,
            ["planned_start", "planned_end", "deadline", "actual_start", "actual_end"],
        )

        tasks.append(
            TaskRowDto(
                id=task["id"],
                name=task["name"],
                priority=task["priority"],
                status=TaskStatus(task["status"]),
                planned_start=dt_fields["planned_start"],
                planned_end=dt_fields["planned_end"],
                deadline=dt_fields["deadline"],
                actual_start=dt_fields["actual_start"],
                actual_end=dt_fields["actual_end"],
                estimated_duration=task.get("estimated_duration"),
                actual_duration_hours=task.get("actual_duration_hours"),
                is_fixed=task.get("is_fixed", False),
                depends_on=task.get("depends_on", []),
                tags=task.get("tags", []),
                is_archived=task.get("is_archived", False),
                is_finished=task.get("is_finished", False),
                created_at=_parse_required_datetime(task, "created_at"),
                updated_at=_parse_required_datetime(task, "updated_at"),
            )
        )

    # Convert gantt data if present
    gantt_data = None
    if data.get("gantt"):
        gantt_data = convert_to_gantt_output(data["gantt"])

    return TaskListOutput(
        tasks=tasks,
        total_count=data["total_count"],
        filtered_count=data["filtered_count"],
        gantt_data=gantt_data,
    )


def convert_to_get_task_by_id_output(data: dict[str, Any]) -> TaskByIdOutput:
    """Convert API response to TaskByIdOutput.

    Args:
        data: API response data

    Returns:
        TaskByIdOutput with task data
    """
    task = _build_task_detail_dto(data)
    return TaskByIdOutput(task=task)


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
    has_notes = notes_content is not None and notes_content != ""

    return TaskDetailOutput(task=task, notes_content=notes_content, has_notes=has_notes)
