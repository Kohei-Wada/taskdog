"""Bulk operation endpoints for batch task processing."""

from dataclasses import dataclass

from fastapi import APIRouter

from taskdog_core.application.dto.bulk_operation_output import BulkOperationOutput
from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    BulkTaskControllerDep,
    EventBroadcasterDep,
)
from taskdog_server.api.models.requests import BulkTaskIdsRequest
from taskdog_server.api.models.responses import (
    BulkOperationResponse,
    BulkTaskResult,
    TaskOperationResponse,
)
from taskdog_server.websocket.broadcaster import WebSocketEventBroadcaster

router = APIRouter()


@dataclass(frozen=True)
class BulkLifecycleOperation:
    """Configuration for a bulk lifecycle endpoint."""

    name: str
    description: str


@dataclass(frozen=True)
class BulkCrudOperation:
    """Configuration for a bulk CRUD endpoint."""

    name: str
    description: str
    audit_operation: str


LIFECYCLE_OPERATIONS = [
    BulkLifecycleOperation("start", "Start multiple tasks"),
    BulkLifecycleOperation("complete", "Complete multiple tasks"),
    BulkLifecycleOperation("pause", "Pause multiple tasks"),
    BulkLifecycleOperation("cancel", "Cancel multiple tasks"),
    BulkLifecycleOperation("reopen", "Reopen multiple tasks"),
]

CRUD_OPERATIONS = [
    BulkCrudOperation("archive", "Archive multiple tasks", "archive_task"),
    BulkCrudOperation("restore", "Restore multiple tasks", "restore_task"),
    BulkCrudOperation("delete", "Delete multiple tasks permanently", "delete_task"),
]


def _to_response(output: BulkOperationOutput) -> BulkOperationResponse:
    """Convert core DTO to Pydantic response model."""
    return BulkOperationResponse(
        results=[
            BulkTaskResult(
                task_id=r.task_id,
                success=r.success,
                task=TaskOperationResponse.from_dto(r.task) if r.task else None,
                error=r.error,
            )
            for r in output.results
        ]
    )


def _broadcast(
    broadcaster: WebSocketEventBroadcaster,
    operation: str,
    output: BulkOperationOutput,
    task_ids: list[int],
    client_name: str | None,
) -> None:
    """Send a single bulk_operation_completed WebSocket event."""
    success_count = sum(1 for r in output.results if r.success)
    failure_count = sum(1 for r in output.results if not r.success)
    broadcaster.bulk_operation_completed(
        operation=operation,
        success_count=success_count,
        failure_count=failure_count,
        task_ids=task_ids,
        source_user_name=client_name,
    )


def _create_bulk_lifecycle_endpoint(op: BulkLifecycleOperation) -> None:
    """Create and register a bulk lifecycle endpoint."""

    @router.post(
        f"/bulk/{op.name}",
        response_model=BulkOperationResponse,
        summary=op.description,
    )
    async def endpoint(
        request: BulkTaskIdsRequest,
        bulk_controller: BulkTaskControllerDep,
        broadcaster: EventBroadcasterDep,
        audit_controller: AuditLogControllerDep,
        client_name: AuthenticatedClientDep,
    ) -> BulkOperationResponse:
        output = bulk_controller.bulk_lifecycle(request.task_ids, op.name)

        for r in output.results:
            if r.success and r.task is not None:
                audit_controller.log_operation(
                    operation=f"{op.name}_task",
                    resource_type="task",
                    resource_id=r.task_id,
                    resource_name=r.task.name,
                    client_name=client_name,
                    old_values={"status": r.old_status} if r.old_status else None,
                    new_values={"status": r.task.status.value},
                    success=True,
                )

        _broadcast(broadcaster, op.name, output, request.task_ids, client_name)
        return _to_response(output)


def _create_bulk_crud_endpoint(op: BulkCrudOperation) -> None:
    """Create and register a bulk CRUD endpoint."""

    @router.post(
        f"/bulk/{op.name}",
        response_model=BulkOperationResponse,
        summary=op.description,
    )
    async def endpoint(
        request: BulkTaskIdsRequest,
        bulk_controller: BulkTaskControllerDep,
        broadcaster: EventBroadcasterDep,
        audit_controller: AuditLogControllerDep,
        client_name: AuthenticatedClientDep,
    ) -> BulkOperationResponse:
        method = getattr(bulk_controller, f"bulk_{op.name}")
        output: BulkOperationOutput = method(request.task_ids)

        for r in output.results:
            if r.success:
                resource_name = r.task.name if r.task else r.task_name
                old_values = None
                new_values = None
                if op.name == "archive":
                    old_values = {"is_archived": False}
                    new_values = {"is_archived": True}
                elif op.name == "restore":
                    old_values = {"is_archived": True}
                    new_values = {"is_archived": False}
                audit_controller.log_operation(
                    operation=op.audit_operation,
                    resource_type="task",
                    resource_id=r.task_id,
                    resource_name=resource_name,
                    client_name=client_name,
                    old_values=old_values,
                    new_values=new_values,
                    success=True,
                )

        _broadcast(broadcaster, op.name, output, request.task_ids, client_name)
        return _to_response(output)


# Generate all bulk endpoints
for _lifecycle_op in LIFECYCLE_OPERATIONS:
    _create_bulk_lifecycle_endpoint(_lifecycle_op)

for _crud_op in CRUD_OPERATIONS:
    _create_bulk_crud_endpoint(_crud_op)
