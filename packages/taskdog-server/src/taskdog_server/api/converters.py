"""DTO to Pydantic response model converters.

This module contains all conversion functions that transform use case DTOs
from taskdog-core into Pydantic response models for the API.
"""

from taskdog_core.application.dto.gantt_output import GanttOutput
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.shared.utils.datetime_parser import format_date_dict
from taskdog_server.api.models.responses import (
    GanttDateRange,
    GanttResponse,
    GanttTaskResponse,
    TaskDetailResponse,
    TaskListResponse,
    TaskResponse,
    UpdateTaskResponse,
)


def convert_to_update_task_response(dto: TaskUpdateOutput) -> UpdateTaskResponse:
    """Convert TaskUpdateOutput DTO to Pydantic response model."""
    return UpdateTaskResponse.from_dto(dto)


def convert_to_gantt_response(gantt_output: GanttOutput) -> GanttResponse:
    """Convert GanttOutput DTO to Pydantic response model.

    Args:
        gantt_output: GanttOutput DTO from controller

    Returns:
        GanttResponse with all date keys converted to ISO format strings
    """
    # Convert tasks
    gantt_tasks = [
        GanttTaskResponse(
            id=task.id,
            name=task.name,
            status=task.status,
            estimated_duration=task.estimated_duration,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            deadline=task.deadline,
            is_fixed=False,  # Not available in GanttTaskDto
            is_archived=False,  # Not available in GanttTaskDto
            daily_allocations=format_date_dict(
                gantt_output.task_daily_hours.get(task.id, {})
            ),
        )
        for task in gantt_output.tasks
    ]

    # Convert task_daily_hours (nested dict with date keys)
    task_daily_hours = {
        task_id: format_date_dict(daily_hours)
        for task_id, daily_hours in gantt_output.task_daily_hours.items()
    }

    # Convert daily_workload
    daily_workload = format_date_dict(gantt_output.daily_workload)

    # Convert holidays (set of dates to list of ISO strings)
    holidays = [holiday.isoformat() for holiday in gantt_output.holidays]

    return GanttResponse(
        date_range=GanttDateRange(
            start_date=gantt_output.date_range.start_date,
            end_date=gantt_output.date_range.end_date,
        ),
        tasks=gantt_tasks,
        task_daily_hours=task_daily_hours,
        daily_workload=daily_workload,
        holidays=holidays,
        total_estimated_duration=gantt_output.total_estimated_duration,
    )


def convert_to_task_list_response(
    dto: TaskListOutput, notes_repo: NotesRepository
) -> TaskListResponse:
    """Convert TaskListOutput DTO to Pydantic response model.

    Args:
        dto: TaskListOutput DTO from controller
        notes_repo: Notes repository for checking note existence

    Returns:
        TaskListResponse with has_notes field populated
    """
    # Batch query for note existence - single query instead of N queries
    task_ids = [task.id for task in dto.tasks]
    task_ids_with_notes = notes_repo.get_task_ids_with_notes(task_ids)

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
