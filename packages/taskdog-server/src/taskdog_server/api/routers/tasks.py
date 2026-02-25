"""CRUD endpoints for task management."""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Query, status

from taskdog_core.application.dto.query_inputs import ListTasksInput
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_server.api.converters import (
    convert_to_task_detail_response,
    convert_to_task_list_response,
    convert_to_update_task_response,
)
from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    CrudControllerDep,
    EventBroadcasterDep,
    HolidayCheckerDep,
    NotesRepositoryDep,
    QueryControllerDep,
)
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.requests import CreateTaskRequest, UpdateTaskRequest
from taskdog_server.api.models.responses import (
    TaskDetailResponse,
    TaskListResponse,
    TaskOperationResponse,
    UpdateTaskResponse,
)
from taskdog_server.api.utils import parse_iso_date

router = APIRouter()


def _serialize_audit_value(val: object) -> object:
    """Serialize a value for JSON-safe audit logging."""
    if hasattr(val, "value"):
        val = val.value
    if isinstance(val, datetime):
        val = val.isoformat()
    if isinstance(val, dict):
        val = {
            k.isoformat() if isinstance(k, (date, datetime)) else k: (
                v.isoformat() if isinstance(v, (date, datetime)) else v
            )
            for k, v in val.items()
        }
    return val


@router.post(
    "", response_model=TaskOperationResponse, status_code=status.HTTP_201_CREATED
)
@handle_task_errors
async def create_task(
    request: CreateTaskRequest,
    controller: CrudControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Create a new task.

    Args:
        request: Task creation data
        controller: CRUD controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Created task data

    Raises:
        HTTPException: 400 if validation fails
    """
    result = controller.create_task(
        name=request.name,
        priority=request.priority,
        planned_start=request.planned_start,
        planned_end=request.planned_end,
        deadline=request.deadline,
        estimated_duration=request.estimated_duration,
        is_fixed=request.is_fixed,
        tags=request.tags,
    )

    # Broadcast WebSocket event in background
    broadcaster.task_created(result, client_name)

    # Audit log
    audit_controller.log_operation(
        operation="create_task",
        resource_type="task",
        resource_id=result.id,
        resource_name=result.name,
        client_name=client_name,
        new_values={
            "name": result.name,
            "priority": result.priority,
            "status": result.status.value,
        },
        success=True,
    )

    return TaskOperationResponse.from_dto(result)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    controller: QueryControllerDep,
    notes_repo: NotesRepositoryDep,
    holiday_checker: HolidayCheckerDep,
    _client_name: AuthenticatedClientDep,
    all: Annotated[bool, Query(description="Include archived tasks")] = False,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    tags: Annotated[
        list[str] | None, Query(description="Filter by tags (OR logic)")
    ] = None,
    start_date: Annotated[str | None, Query(description="Filter by start date")] = None,
    end_date: Annotated[str | None, Query(description="Filter by end date")] = None,
    sort: Annotated[str, Query(description="Sort field")] = "id",
    reverse: Annotated[bool, Query(description="Reverse sort order")] = False,
    include_gantt: Annotated[
        bool, Query(description="Include Gantt chart data in response")
    ] = False,
    gantt_start_date: Annotated[
        str | None, Query(description="Gantt chart start date (ISO format)")
    ] = None,
    gantt_end_date: Annotated[
        str | None, Query(description="Gantt chart end date (ISO format)")
    ] = None,
) -> TaskListResponse:
    """List tasks with optional filtering and sorting.

    Args:
        controller: Query controller dependency
        holiday_checker: Holiday checker dependency
        all: Include archived tasks
        status_filter: Filter by task status
        tags: Filter by tags (OR logic)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        sort: Sort field name
        reverse: Reverse sort order
        include_gantt: Include Gantt chart data
        gantt_start_date: Gantt chart start date (ISO format)
        gantt_end_date: Gantt chart end date (ISO format)

    Returns:
        List of tasks with metadata, optionally including Gantt data
    """
    # Parse date strings to date objects
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)
    gantt_start = parse_iso_date(gantt_start_date)
    gantt_end = parse_iso_date(gantt_end_date)

    # Create Input DTO (filter building is done in Use Case)
    input_dto = ListTasksInput(
        include_archived=all,
        status=status_filter,
        tags=tags or [],
        start_date=start,
        end_date=end,
        sort_by=sort,
        reverse=reverse,
    )

    # Query tasks using Use Case pattern
    result = controller.list_tasks(
        input_dto=input_dto,
        include_gantt=include_gantt,
        gantt_start_date=gantt_start,
        gantt_end_date=gantt_end,
        holiday_checker=holiday_checker if include_gantt else None,
    )
    return convert_to_task_list_response(result, notes_repo)


@router.get("/{task_id}", response_model=TaskDetailResponse)
@handle_task_errors
async def get_task(
    task_id: int,
    controller: QueryControllerDep,
    _client_name: AuthenticatedClientDep,
) -> TaskDetailResponse:
    """Get task details by ID.

    Args:
        task_id: Task ID
        controller: Query controller dependency

    Returns:
        Task detail data including notes

    Raises:
        HTTPException: 404 if task not found
    """
    result = controller.get_task_detail(task_id)
    return convert_to_task_detail_response(result)


@router.patch("/{task_id}", response_model=UpdateTaskResponse)
@handle_task_errors
async def update_task(
    task_id: int,
    request: UpdateTaskRequest,
    controller: CrudControllerDep,
    query_controller: QueryControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> UpdateTaskResponse:
    """Update task fields.

    Args:
        task_id: Task ID
        request: Fields to update (only provided fields are updated)
        controller: CRUD controller dependency
        query_controller: Query controller dependency (for fetching old values)
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    # Get old values before update for audit trail
    # Handle potential errors gracefully - if we can't get old values,
    # proceed with update but log without old values
    try:
        old_task_output = query_controller.get_task_by_id(task_id)
        old_task = old_task_output.task if old_task_output else None
    except Exception:
        old_task = None

    result = controller.update_task(
        task_id=task_id,
        name=request.name,
        priority=request.priority,
        status=request.status,
        planned_start=request.planned_start,
        planned_end=request.planned_end,
        deadline=request.deadline,
        estimated_duration=request.estimated_duration,
        is_fixed=request.is_fixed,
        tags=request.tags,
    )

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result.task, result.updated_fields, client_name)

    # Audit log with old/new values for updated fields
    old_values = {}
    new_values = {}
    if old_task:
        for field in result.updated_fields:
            if hasattr(old_task, field) and hasattr(result.task, field):
                old_values[field] = _serialize_audit_value(getattr(old_task, field))
                new_values[field] = _serialize_audit_value(getattr(result.task, field))

    audit_controller.log_operation(
        operation="update_task",
        resource_type="task",
        resource_id=task_id,
        resource_name=result.task.name,
        client_name=client_name,
        old_values=old_values if old_values else None,
        new_values=new_values if new_values else None,
        success=True,
    )

    return convert_to_update_task_response(result)


@router.post("/{task_id}/archive", response_model=TaskOperationResponse)
@handle_task_errors
async def archive_task(
    task_id: int,
    controller: CrudControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Archive (soft delete) a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Archived task data

    Raises:
        HTTPException: 404 if task not found
    """
    result = controller.archive_task(task_id)

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["is_archived"], client_name)

    # Audit log
    audit_controller.log_operation(
        operation="archive_task",
        resource_type="task",
        resource_id=task_id,
        resource_name=result.name,
        client_name=client_name,
        old_values={"is_archived": False},
        new_values={"is_archived": True},
        success=True,
    )

    return TaskOperationResponse.from_dto(result)


@router.post("/{task_id}/restore", response_model=TaskOperationResponse)
@handle_task_errors
async def restore_task(
    task_id: int,
    controller: CrudControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Restore an archived task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Restored task data

    Raises:
        HTTPException: 404 if task not found, 400 if not archived
    """
    result = controller.restore_task(task_id)

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["is_archived"], client_name)

    # Audit log
    audit_controller.log_operation(
        operation="restore_task",
        resource_type="task",
        resource_id=task_id,
        resource_name=result.name,
        client_name=client_name,
        old_values={"is_archived": True},
        new_values={"is_archived": False},
        success=True,
    )

    return TaskOperationResponse.from_dto(result)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_task_errors
async def delete_task(
    task_id: int,
    controller: CrudControllerDep,
    query_controller: QueryControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> None:
    """Permanently delete a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        query_controller: Query controller dependency (for fetching task name before deletion)
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Raises:
        HTTPException: 404 if task not found
    """
    # Get task name before deletion for notification
    task_output = query_controller.get_task_by_id(task_id)
    if task_output is None or task_output.task is None:
        raise TaskNotFoundException(f"Task {task_id} not found")
    task_name = task_output.task.name

    # Delete task
    controller.remove_task(task_id)

    # Broadcast WebSocket event in background
    broadcaster.task_deleted(task_id, task_name, client_name)

    # Audit log
    audit_controller.log_operation(
        operation="delete_task",
        resource_type="task",
        resource_id=task_id,
        resource_name=task_name,
        client_name=client_name,
        success=True,
    )
