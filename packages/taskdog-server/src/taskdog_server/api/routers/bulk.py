"""Bulk operation endpoints for batch task processing."""

from dataclasses import dataclass

from fastapi import APIRouter

from taskdog_core.controllers.audit_log_controller import AuditLogController
from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
    TaskValidationError,
)
from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    CrudControllerDep,
    EventBroadcasterDep,
    LifecycleControllerDep,
    QueryControllerDep,
)
from taskdog_server.api.models.requests import BulkTaskIdsRequest
from taskdog_server.api.models.responses import (
    BulkOperationResponse,
    BulkTaskResult,
    TaskOperationResponse,
)
from taskdog_server.websocket.broadcaster import WebSocketEventBroadcaster

router = APIRouter()

_TASK_ERRORS = (
    TaskNotFoundException,
    TaskValidationError,
    TaskAlreadyFinishedError,
    TaskNotStartedError,
)


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


LIFECYCLE_OPERATIONS = [
    BulkLifecycleOperation("start", "Start multiple tasks"),
    BulkLifecycleOperation("complete", "Complete multiple tasks"),
    BulkLifecycleOperation("pause", "Pause multiple tasks"),
    BulkLifecycleOperation("cancel", "Cancel multiple tasks"),
    BulkLifecycleOperation("reopen", "Reopen multiple tasks"),
]

CRUD_OPERATIONS = [
    BulkCrudOperation("archive", "Archive multiple tasks"),
    BulkCrudOperation("restore", "Restore multiple tasks"),
    BulkCrudOperation("delete", "Delete multiple tasks permanently"),
]


def _execute_bulk_lifecycle(
    task_ids: list[int],
    operation_name: str,
    controller: TaskLifecycleController,
    broadcaster: WebSocketEventBroadcaster,
    audit_controller: AuditLogController,
    client_name: str | None,
) -> BulkOperationResponse:
    """Execute a lifecycle operation on multiple tasks."""
    results: list[BulkTaskResult] = []

    method_name = f"{operation_name}_task"
    if not hasattr(controller, method_name):
        raise ValueError(f"Invalid lifecycle operation: {operation_name}")

    for task_id in task_ids:
        try:
            controller_method = getattr(controller, method_name)
            result = controller_method(task_id)

            audit_controller.log_operation(
                operation=f"{operation_name}_task",
                resource_type="task",
                resource_id=task_id,
                resource_name=result.task.name,
                client_name=client_name,
                old_values={"status": result.old_status.value},
                new_values={"status": result.task.status.value},
                success=True,
            )

            results.append(
                BulkTaskResult(
                    task_id=task_id,
                    success=True,
                    task=TaskOperationResponse.from_dto(result.task),
                )
            )
        except _TASK_ERRORS as e:
            results.append(
                BulkTaskResult(
                    task_id=task_id,
                    success=False,
                    error=str(e),
                )
            )

    success_ids = [r.task_id for r in results if r.success]
    failure_count = sum(1 for r in results if not r.success)
    broadcaster.bulk_operation_completed(
        operation=operation_name,
        success_count=len(success_ids),
        failure_count=failure_count,
        task_ids=task_ids,
        source_user_name=client_name,
    )

    return BulkOperationResponse(results=results)


def _execute_bulk_crud(
    task_ids: list[int],
    operation_name: str,
    controller: TaskCrudController,
    query_controller: QueryController,
    broadcaster: WebSocketEventBroadcaster,
    audit_controller: AuditLogController,
    client_name: str | None,
) -> BulkOperationResponse:
    """Execute a CRUD operation (archive/restore/delete) on multiple tasks."""
    results: list[BulkTaskResult] = []

    for task_id in task_ids:
        try:
            if operation_name == "archive":
                result = controller.archive_task(task_id)
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
                results.append(
                    BulkTaskResult(
                        task_id=task_id,
                        success=True,
                        task=TaskOperationResponse.from_dto(result),
                    )
                )

            elif operation_name == "restore":
                result = controller.restore_task(task_id)
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
                results.append(
                    BulkTaskResult(
                        task_id=task_id,
                        success=True,
                        task=TaskOperationResponse.from_dto(result),
                    )
                )

            elif operation_name == "delete":
                task_output = query_controller.get_task_by_id(task_id)
                if task_output is None or task_output.task is None:
                    raise TaskNotFoundException(f"Task {task_id} not found")
                task_name = task_output.task.name
                controller.remove_task(task_id)
                audit_controller.log_operation(
                    operation="delete_task",
                    resource_type="task",
                    resource_id=task_id,
                    resource_name=task_name,
                    client_name=client_name,
                    success=True,
                )
                results.append(
                    BulkTaskResult(
                        task_id=task_id,
                        success=True,
                    )
                )

            else:
                raise ValueError(f"Invalid CRUD operation: {operation_name}")

        except _TASK_ERRORS as e:
            results.append(
                BulkTaskResult(
                    task_id=task_id,
                    success=False,
                    error=str(e),
                )
            )

    success_ids = [r.task_id for r in results if r.success]
    failure_count = sum(1 for r in results if not r.success)
    broadcaster.bulk_operation_completed(
        operation=operation_name,
        success_count=len(success_ids),
        failure_count=failure_count,
        task_ids=task_ids,
        source_user_name=client_name,
    )

    return BulkOperationResponse(results=results)


def _create_bulk_lifecycle_endpoint(op: BulkLifecycleOperation) -> None:
    """Create and register a bulk lifecycle endpoint."""

    @router.post(
        f"/bulk/{op.name}",
        response_model=BulkOperationResponse,
        summary=op.description,
    )
    async def endpoint(
        request: BulkTaskIdsRequest,
        controller: LifecycleControllerDep,
        broadcaster: EventBroadcasterDep,
        audit_controller: AuditLogControllerDep,
        client_name: AuthenticatedClientDep,
    ) -> BulkOperationResponse:
        return _execute_bulk_lifecycle(
            request.task_ids,
            op.name,
            controller,
            broadcaster,
            audit_controller,
            client_name,
        )


def _create_bulk_crud_endpoint(op: BulkCrudOperation) -> None:
    """Create and register a bulk CRUD endpoint."""

    @router.post(
        f"/bulk/{op.name}",
        response_model=BulkOperationResponse,
        summary=op.description,
    )
    async def endpoint(
        request: BulkTaskIdsRequest,
        controller: CrudControllerDep,
        query_controller: QueryControllerDep,
        broadcaster: EventBroadcasterDep,
        audit_controller: AuditLogControllerDep,
        client_name: AuthenticatedClientDep,
    ) -> BulkOperationResponse:
        return _execute_bulk_crud(
            request.task_ids,
            op.name,
            controller,
            query_controller,
            broadcaster,
            audit_controller,
            client_name,
        )


# Generate all bulk endpoints
for _lifecycle_op in LIFECYCLE_OPERATIONS:
    _create_bulk_lifecycle_endpoint(_lifecycle_op)

for _crud_op in CRUD_OPERATIONS:
    _create_bulk_crud_endpoint(_crud_op)
