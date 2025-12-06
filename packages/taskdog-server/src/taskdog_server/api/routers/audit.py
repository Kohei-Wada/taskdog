"""Audit log endpoints for viewing operation history."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from taskdog_core.application.dto.audit_log_dto import AuditQuery
from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
)
from taskdog_server.api.models.responses import AuditLogListResponse, AuditLogResponse
from taskdog_server.api.utils import parse_iso_datetime

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    controller: AuditLogControllerDep,
    _client_name: AuthenticatedClientDep,
    client_filter: Annotated[
        str | None, Query(alias="client", description="Filter by client name")
    ] = None,
    operation: Annotated[
        str | None, Query(description="Filter by operation type")
    ] = None,
    resource_type: Annotated[
        str | None, Query(description="Filter by resource type")
    ] = None,
    resource_id: Annotated[
        int | None, Query(description="Filter by resource ID")
    ] = None,
    success: Annotated[
        bool | None, Query(description="Filter by success status")
    ] = None,
    start_date: Annotated[
        str | None, Query(description="Filter by start datetime (ISO format)")
    ] = None,
    end_date: Annotated[
        str | None, Query(description="Filter by end datetime (ISO format)")
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum number of logs to return")
    ] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of logs to skip")] = 0,
) -> AuditLogListResponse:
    """List audit logs with optional filtering.

    Args:
        controller: Audit log controller dependency
        client_filter: Filter by client name (e.g., "claude-code")
        operation: Filter by operation type (e.g., "create_task", "complete_task")
        resource_type: Filter by resource type (e.g., "task", "schedule")
        resource_id: Filter by resource ID (e.g., task ID)
        success: Filter by success status
        start_date: Filter logs after this datetime (ISO format)
        end_date: Filter logs before this datetime (ISO format)
        limit: Maximum number of logs to return (1-1000, default 100)
        offset: Number of logs to skip for pagination (default 0)

    Returns:
        AuditLogListResponse with logs and pagination info
    """
    # Parse date strings to datetime objects
    start = parse_iso_datetime(start_date)
    end = parse_iso_datetime(end_date)

    # Build query
    query = AuditQuery(
        client_name=client_filter,
        operation=operation,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
        start_date=start,
        end_date=end,
        limit=limit,
        offset=offset,
    )

    # Execute query
    result = controller.get_logs(query)

    # Convert to response models
    logs = [
        AuditLogResponse(
            id=log.id,
            timestamp=log.timestamp,
            client_name=log.client_name,
            operation=log.operation,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            resource_name=log.resource_name,
            old_values=log.old_values,
            new_values=log.new_values,
            success=log.success,
            error_message=log.error_message,
        )
        for log in result.logs
    ]

    return AuditLogListResponse(
        logs=logs,
        total_count=result.total_count,
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    controller: AuditLogControllerDep,
    _client_name: AuthenticatedClientDep,
) -> AuditLogResponse:
    """Get a single audit log entry by ID.

    Args:
        log_id: Audit log ID
        controller: Audit log controller dependency

    Returns:
        AuditLogResponse if found

    Raises:
        HTTPException: 404 if audit log not found
    """
    result = controller.get_by_id(log_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log {log_id} not found",
        )

    return AuditLogResponse(
        id=result.id,
        timestamp=result.timestamp,
        client_name=result.client_name,
        operation=result.operation,
        resource_type=result.resource_type,
        resource_id=result.resource_id,
        resource_name=result.resource_name,
        old_values=result.old_values,
        new_values=result.new_values,
        success=result.success,
        error_message=result.error_message,
    )
