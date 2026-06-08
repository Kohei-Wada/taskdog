"""DTO to Pydantic response model converters.

This module contains all conversion functions that transform use case DTOs
from taskdog-core into Pydantic response models for the API.
"""

from taskdog_core.application.dto.gantt_overlay import GanttOverlay
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.shared.utils.datetime_parser import format_date_dict
from taskdog_server.api.models.responses import (
    GanttDateRange,
    GanttResponse,
    TaskDetailResponse,
    TaskListResponse,
    TaskResponse,
    UpdateTaskResponse,
)


def convert_to_update_task_response(dto: TaskUpdateOutput) -> UpdateTaskResponse:
    """Convert TaskUpdateOutput DTO to Pydantic response model."""
    return UpdateTaskResponse.from_dto(dto)


def convert_to_gantt_response(overlay: GanttOverlay) -> GanttResponse:
    """Convert a GanttOverlay DTO to its Pydantic response model.

    The overlay carries no task data; clients join it with the shared task
    list by id.

    Args:
        overlay: GanttOverlay DTO from the controller

    Returns:
        GanttResponse with all date keys converted to ISO format strings
    """
    # Convert task_daily_hours (nested dict with date keys)
    task_daily_hours = {
        task_id: format_date_dict(daily_hours)
        for task_id, daily_hours in overlay.task_daily_hours.items()
    }

    # Convert daily_workload
    daily_workload = format_date_dict(overlay.daily_workload)

    # Convert holidays (set of dates to list of ISO strings)
    holidays = [holiday.isoformat() for holiday in overlay.holidays]

    return GanttResponse(
        date_range=GanttDateRange(
            start_date=overlay.date_range.start_date,
            end_date=overlay.date_range.end_date,
        ),
        task_daily_hours=task_daily_hours,
        daily_workload=daily_workload,
        holidays=holidays,
        total_estimated_duration=overlay.total_estimated_duration,
    )


def convert_to_task_list_response(dto: TaskListOutput) -> TaskListResponse:
    """Convert TaskListOutput DTO to Pydantic response model.

    Args:
        dto: TaskListOutput DTO from controller

    Returns:
        TaskListResponse with has_notes field populated
    """
    task_ids_with_notes = dto.task_ids_with_notes or set()

    tasks = [
        TaskResponse(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            estimated_duration=task.estimated_duration,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            actual_duration_hours=task.actual_duration_hours,
            depends_on=task.depends_on,
            tags=task.tags,
            is_fixed=task.is_fixed,
            daily_allocations=format_date_dict(task.daily_allocations),
            is_archived=task.is_archived,
            is_finished=task.is_finished,
            has_notes=task.id in task_ids_with_notes,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in dto.tasks
    ]

    # Convert gantt_data if present
    gantt = None
    if dto.gantt_data:
        gantt = convert_to_gantt_response(dto.gantt_data)

    return TaskListResponse(
        tasks=tasks,
        total_count=dto.total_count,
        filtered_count=dto.filtered_count,
        gantt=gantt,
    )


def convert_to_task_detail_response(dto: TaskDetailOutput) -> TaskDetailResponse:
    """Convert TaskDetailOutput DTO to Pydantic response model."""
    return TaskDetailResponse.from_dto(dto)
