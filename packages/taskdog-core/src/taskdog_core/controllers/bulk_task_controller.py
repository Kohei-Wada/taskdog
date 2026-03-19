"""Bulk task controller for batch operations.

Moves loop + error handling logic from the server layer into core,
keeping audit logging and WebSocket broadcasting in the server layer.
"""

from taskdog_core.application.dto.bulk_operation_output import (
    BulkOperationOutput,
    BulkTaskResultOutput,
)
from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
    TaskValidationError,
)

_TASK_ERRORS = (
    TaskNotFoundException,
    TaskValidationError,
    TaskAlreadyFinishedError,
    TaskNotStartedError,
)

_LIFECYCLE_OPERATIONS = frozenset({"start", "complete", "pause", "cancel", "reopen"})


class BulkTaskController:
    """Controller for batch task operations.

    Encapsulates the loop + per-task error handling for bulk operations.
    Returns core DTOs; the server layer is responsible for audit logging
    and WebSocket broadcasting.
    """

    def __init__(
        self,
        lifecycle_controller: TaskLifecycleController,
        crud_controller: TaskCrudController,
        query_controller: QueryController,
    ) -> None:
        self._lifecycle = lifecycle_controller
        self._crud = crud_controller
        self._query = query_controller

    def bulk_lifecycle(
        self, task_ids: list[int], operation: str
    ) -> BulkOperationOutput:
        """Execute a lifecycle operation on multiple tasks.

        Args:
            task_ids: IDs of tasks to operate on.
            operation: One of start, complete, pause, cancel, reopen.

        Returns:
            BulkOperationOutput with per-task results.

        Raises:
            ValueError: If operation is not a valid lifecycle operation.
        """
        if operation not in _LIFECYCLE_OPERATIONS:
            raise ValueError(f"Invalid lifecycle operation: {operation}")

        method_name = f"{operation}_task"
        controller_method = getattr(self._lifecycle, method_name)

        results: list[BulkTaskResultOutput] = []
        for task_id in task_ids:
            try:
                result = controller_method(task_id)
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=True,
                        task=result.task,
                        error=None,
                        old_status=result.old_status.value,
                    )
                )
            except _TASK_ERRORS as e:
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=False,
                        task=None,
                        error=str(e),
                    )
                )

        return BulkOperationOutput(results=results)

    def bulk_archive(self, task_ids: list[int]) -> BulkOperationOutput:
        """Archive multiple tasks (soft delete)."""
        results: list[BulkTaskResultOutput] = []
        for task_id in task_ids:
            try:
                result = self._crud.archive_task(task_id)
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=True,
                        task=result,
                        error=None,
                    )
                )
            except _TASK_ERRORS as e:
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=False,
                        task=None,
                        error=str(e),
                    )
                )
        return BulkOperationOutput(results=results)

    def bulk_restore(self, task_ids: list[int]) -> BulkOperationOutput:
        """Restore multiple archived tasks."""
        results: list[BulkTaskResultOutput] = []
        for task_id in task_ids:
            try:
                result = self._crud.restore_task(task_id)
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=True,
                        task=result,
                        error=None,
                    )
                )
            except _TASK_ERRORS as e:
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=False,
                        task=None,
                        error=str(e),
                    )
                )
        return BulkOperationOutput(results=results)

    def bulk_delete(self, task_ids: list[int]) -> BulkOperationOutput:
        """Hard delete multiple tasks.

        Looks up the task name before deletion so callers can use it
        for audit logging.
        """
        results: list[BulkTaskResultOutput] = []
        for task_id in task_ids:
            try:
                task_output = self._query.get_task_by_id(task_id)
                if task_output is None or task_output.task is None:
                    raise TaskNotFoundException(f"Task {task_id} not found")
                name = task_output.task.name
                self._crud.remove_task(task_id)
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=True,
                        task=None,
                        error=None,
                        task_name=name,
                    )
                )
            except _TASK_ERRORS as e:
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=False,
                        task=None,
                        error=str(e),
                    )
                )
        return BulkOperationOutput(results=results)
