"""CRUD endpoints for task management."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from taskdog_core.application.dto.query_inputs import ListTasksInput
from taskdog_server.api.audit_helpers import (
    capture_old_task,
    diff_task_fields,
    log_task_operation,
)
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
    QueryControllerDep,
)
from taskdog_server.api.models.requests import CreateTaskRequest, UpdateTaskRequest
from taskdog_server.api.models.responses import (
    TaskDetailResponse,
    TaskListResponse,
    TaskOperationResponse,
    UpdateTaskResponse,
)
from taskdog_server.api.utils import parse_iso_date

router = APIRouter()


@router.post(
    "", response_model=TaskOperationResponse, status_code=status.HTTP_201_CREATED
)
def create_task(
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

    log_task_operation(
        audit_controller,
        operation="create_task",
        task=result,
        client_name=client_name,
        new_values={
            "name": result.name,
            "priority": result.priority,
            "status": result.status.value,
        },
    )

    return TaskOperationResponse.from_dto(result)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    controller: QueryControllerDep,
    holiday_checker: HolidayCheckerDep,
    _client_name: AuthenticatedClientDep,
    include_archived: Annotated[
        bool, Query(alias="all", description="Include archived tasks")
    ] = False,
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
        include_archived: Include archived tasks
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
        include_archived=include_archived,
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
    return convert_to_task_list_response(result)


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(
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
def update_task(
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
    # Get old values before update for audit trail; if unavailable, the update
    # still proceeds and is logged without old values.
    old_task = capture_old_task(query_controller, task_id)

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

    old_values, new_values = diff_task_fields(
        old_task, result.task, result.updated_fields
    )
    log_task_operation(
        audit_controller,
        operation="update_task",
        task=result.task,
        client_name=client_name,
        old_values=old_values,
        new_values=new_values,
    )

    return convert_to_update_task_response(result)


@router.post("/{task_id}/archive", response_model=TaskOperationResponse)
def archive_task(
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

    log_task_operation(
        audit_controller,
        operation="archive_task",
        task=result,
        client_name=client_name,
        old_values={"is_archived": False},
        new_values={"is_archived": True},
    )

    return TaskOperationResponse.from_dto(result)


@router.post("/{task_id}/restore", response_model=TaskOperationResponse)
def restore_task(
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

    log_task_operation(
        audit_controller,
        operation="restore_task",
        task=result,
        client_name=client_name,
        old_values={"is_archived": True},
        new_values={"is_archived": False},
    )

    return TaskOperationResponse.from_dto(result)


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    controller: CrudControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Permanently delete a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Deleted task data

    Raises:
        HTTPException: 404 if task not found
    """
    result = controller.remove_task(task_id)

    # Broadcast WebSocket event in background
    broadcaster.task_deleted(task_id, result.name, client_name)

    log_task_operation(
        audit_controller,
        operation="delete_task",
        task=result,
        client_name=client_name,
    )

    return TaskOperationResponse.from_dto(result)
