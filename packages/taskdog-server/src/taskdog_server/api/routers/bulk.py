"""Bulk task operation endpoints."""

import logging
from collections.abc import Callable

from fastapi import APIRouter

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    EventBroadcasterDep,
    LifecycleControllerDep,
)
from taskdog_server.api.models.requests import BulkTaskIdsRequest
from taskdog_server.api.models.responses import (
    BulkOperationResponse,
    BulkTaskResult,
    TaskOperationResponse,
)
from taskdog_server.websocket.broadcaster import WebSocketEventBroadcaster

logger = logging.getLogger(__name__)

router = APIRouter()


def _execute_bulk_operation(
    *,
    operation: str,
    task_ids: list[int],
    controller: TaskLifecycleController,
    broadcaster: WebSocketEventBroadcaster,
    audit_controller: AuditLogControllerDep,
    client_name: str | None,
    execute_fn: Callable[[int], TaskOperationOutput],
    old_status: str,
) -> BulkOperationResponse:
    """Execute a bulk operation on multiple tasks.

    Processes each task individually, collecting successes and failures.
    Never raises on per-task errors — returns partial success results.

    Args:
        operation: Operation name (e.g., "start")
        task_ids: List of task IDs to operate on
        controller: Lifecycle controller
        broadcaster: WebSocket event broadcaster
        audit_controller: Audit log controller
        client_name: Authenticated client name
        execute_fn: Function that executes the operation on a single task ID
        old_status: Previous status string for broadcast/audit

    Returns:
        BulkOperationResponse with per-task results
    """
    results: list[BulkTaskResult] = []
    succeeded = 0
    failed = 0

    for task_id in task_ids:
        try:
            result = execute_fn(task_id)
            broadcaster.task_status_changed(result, old_status, client_name)
            audit_controller.log_operation(
                operation=f"{operation}_task",
                resource_type="task",
                resource_id=task_id,
                resource_name=result.name,
                client_name=client_name,
                old_values={"status": old_status},
                new_values={"status": result.status.value},
                success=True,
            )
            results.append(
                BulkTaskResult(
                    task_id=task_id,
                    success=True,
                    task=TaskOperationResponse.from_dto(result),
                )
            )
            succeeded += 1
        except Exception as e:
            audit_controller.log_operation(
                operation=f"{operation}_task",
                resource_type="task",
                resource_id=task_id,
                resource_name=None,
                client_name=client_name,
                old_values=None,
                new_values=None,
                success=False,
                error_message=str(e),
            )
            results.append(
                BulkTaskResult(
                    task_id=task_id,
                    success=False,
                    error=str(e),
                )
            )
            failed += 1

    return BulkOperationResponse(
        operation=operation,
        total=len(task_ids),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


@router.post("/start", response_model=BulkOperationResponse)
async def bulk_start(
    request: BulkTaskIdsRequest,
    controller: LifecycleControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> BulkOperationResponse:
    """Start multiple tasks in a single request.

    Processes each task individually. Returns partial success results
    if some tasks fail (e.g., not found, already started).

    Args:
        request: Request with list of task IDs
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name

    Returns:
        BulkOperationResponse with per-task results
    """
    return _execute_bulk_operation(
        operation="start",
        task_ids=request.task_ids,
        controller=controller,
        broadcaster=broadcaster,
        audit_controller=audit_controller,
        client_name=client_name,
        execute_fn=controller.start_task,
        old_status="PENDING",
    )
