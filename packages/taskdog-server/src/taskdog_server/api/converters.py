"""DTO to Pydantic response model converters.

This module contains all conversion functions that transform use case DTOs
from taskdog-core into Pydantic response models for the API.
"""

from taskdog_server.api.models.responses import (
    GanttDateRange,
    GanttResponse,
    GanttTaskResponse,
    TaskDetailResponse,
    TaskListResponse,
    TaskOperationResponse,
    TaskResponse,
    UpdateTaskResponse,
)


def convert_to_task_operation_response(dto) -> TaskOperationResponse:
    """Convert TaskOperationOutput DTO to Pydantic response model."""
    return TaskOperationResponse(
        id=dto.id,
        name=dto.name,
        status=dto.status,
        priority=dto.priority,
        deadline=dto.deadline,
        estimated_duration=dto.estimated_duration,
        planned_start=dto.planned_start,
        planned_end=dto.planned_end,
        actual_start=dto.actual_start,
        actual_end=dto.actual_end,
        depends_on=dto.depends_on,
        tags=dto.tags,
        is_fixed=dto.is_fixed,
        is_archived=dto.is_archived,
        actual_duration_hours=dto.actual_duration_hours,
        actual_daily_hours=dto.actual_daily_hours,
    )


def convert_to_update_task_response(dto) -> UpdateTaskResponse:
    """Convert UpdateTaskOutput DTO to Pydantic response model."""
    task = dto.task  # UpdateTaskOutput has nested task attribute
    return UpdateTaskResponse(
        id=task.id,
        name=task.name,
        status=task.status,
        priority=task.priority,
        deadline=task.deadline,
        estimated_duration=task.estimated_duration,
        planned_start=task.planned_start,
        planned_end=task.planned_end,
        actual_start=task.actual_start,
        actual_end=task.actual_end,
        depends_on=task.depends_on,
        tags=task.tags,
        is_fixed=task.is_fixed,
        is_archived=task.is_archived,
        actual_duration_hours=task.actual_duration_hours,
        actual_daily_hours=task.actual_daily_hours,
        updated_fields=dto.updated_fields,
    )


def convert_to_task_list_response(dto, notes_repo) -> TaskListResponse:
    """Convert TaskListOutput DTO to Pydantic response model.

    Args:
        dto: TaskListOutput DTO from controller
        notes_repo: Notes repository for checking note existence

    Returns:
        TaskListResponse with has_notes field populated
    """
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
            has_notes=notes_repo.has_notes(task.id),
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in dto.tasks
    ]

    # Convert gantt_data if present
    gantt = None
    if dto.gantt_data:
        result = dto.gantt_data
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
                daily_allocations={
                    date_obj.isoformat(): hours
                    for date_obj, hours in result.task_daily_hours.get(
                        task.id, {}
                    ).items()
                },
            )
            for task in result.tasks
        ]

        # Convert task_daily_hours (nested dict with date keys)
        task_daily_hours = {
            task_id: {
                date_obj.isoformat(): hours for date_obj, hours in daily_hours.items()
            }
            for task_id, daily_hours in result.task_daily_hours.items()
        }

        # Convert daily_workload
        daily_workload = {
            date_obj.isoformat(): hours
            for date_obj, hours in result.daily_workload.items()
        }

        # Convert holidays (set of dates to list of ISO strings)
        holidays = [holiday.isoformat() for holiday in result.holidays]

        gantt = GanttResponse(
            date_range=GanttDateRange(
                start_date=result.date_range.start_date,
                end_date=result.date_range.end_date,
            ),
            tasks=gantt_tasks,
            task_daily_hours=task_daily_hours,
            daily_workload=daily_workload,
            holidays=holidays,
        )

    return TaskListResponse(
        tasks=tasks,
        total_count=dto.total_count,
        filtered_count=dto.filtered_count,
        gantt=gantt,
    )


def convert_to_task_detail_response(dto) -> TaskDetailResponse:
    """Convert GetTaskDetailOutput DTO to Pydantic response model."""
    return TaskDetailResponse(
        id=dto.task.id,
        name=dto.task.name,
        priority=dto.task.priority,
        status=dto.task.status,
        planned_start=dto.task.planned_start,
        planned_end=dto.task.planned_end,
        deadline=dto.task.deadline,
        estimated_duration=dto.task.estimated_duration,
        actual_start=dto.task.actual_start,
        actual_end=dto.task.actual_end,
        depends_on=dto.task.depends_on,
        tags=dto.task.tags,
        is_fixed=dto.task.is_fixed,
        is_archived=dto.task.is_archived,
        daily_allocations={
            date.isoformat(): hours
            for date, hours in dto.task.daily_allocations.items()
        },
        actual_daily_hours={
            date.isoformat(): hours
            for date, hours in dto.task.actual_daily_hours.items()
        },
        actual_duration_hours=dto.task.actual_duration_hours,
        is_active=dto.task.is_active,
        is_finished=dto.task.is_finished,
        can_be_modified=dto.task.can_be_modified,
        is_schedulable=dto.task.is_schedulable,
        notes=dto.notes_content,
        created_at=dto.task.created_at,
        updated_at=dto.task.updated_at,
    )
