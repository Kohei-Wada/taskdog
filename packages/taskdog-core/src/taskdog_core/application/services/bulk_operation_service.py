"""Bulk operation service for batch task operations.

Orchestrates per-task use cases in a loop with per-task error handling,
returning core DTOs. The server layer is responsible for audit logging and
WebSocket broadcasting.
"""

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.bulk_operation_output import (
    BulkOperationOutput,
    BulkTaskResultOutput,
)
from taskdog_core.application.use_cases.archive_task import ArchiveTaskUseCase
from taskdog_core.application.use_cases.cancel_task import CancelTaskUseCase
from taskdog_core.application.use_cases.complete_task import CompleteTaskUseCase
from taskdog_core.application.use_cases.pause_task import PauseTaskUseCase
from taskdog_core.application.use_cases.remove_task import RemoveTaskUseCase
from taskdog_core.application.use_cases.reopen_task import ReopenTaskUseCase
from taskdog_core.application.use_cases.restore_task import RestoreTaskUseCase
from taskdog_core.application.use_cases.start_task import StartTaskUseCase
from taskdog_core.application.use_cases.status_change_use_case import (
    StatusChangeUseCase,
)
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
    TaskValidationError,
)
from taskdog_core.domain.repositories.task_repository import TaskRepository

_TASK_ERRORS = (
    TaskNotFoundException,
    TaskValidationError,
    TaskAlreadyFinishedError,
    TaskNotStartedError,
)

_LIFECYCLE_USE_CASES: dict[str, type[StatusChangeUseCase[SingleTaskInput]]] = {
    "start": StartTaskUseCase,
    "complete": CompleteTaskUseCase,
    "pause": PauseTaskUseCase,
    "cancel": CancelTaskUseCase,
    "reopen": ReopenTaskUseCase,
}


class BulkOperationService:
    """Application service for batch task operations.

    Encapsulates the loop + per-task error handling for bulk operations,
    delegating each task to the appropriate use case. Returns core DTOs; the
    server layer is responsible for audit logging and WebSocket broadcasting.
    """

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

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
        use_case_cls = _LIFECYCLE_USE_CASES.get(operation)
        if use_case_cls is None:
            raise ValueError(f"Invalid lifecycle operation: {operation}")

        results: list[BulkTaskResultOutput] = []
        for task_id in task_ids:
            try:
                result = use_case_cls(self._repository).execute(
                    SingleTaskInput(task_id=task_id)
                )
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
                result = ArchiveTaskUseCase(self._repository).execute(
                    SingleTaskInput(task_id=task_id)
                )
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
                result = RestoreTaskUseCase(self._repository).execute(
                    SingleTaskInput(task_id=task_id)
                )
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

        The removal use case captures the task info (including name) before
        deletion, so callers can use ``task_name`` for audit logging.
        """
        results: list[BulkTaskResultOutput] = []
        for task_id in task_ids:
            try:
                result = RemoveTaskUseCase(self._repository).execute(
                    SingleTaskInput(task_id=task_id)
                )
                results.append(
                    BulkTaskResultOutput(
                        task_id=task_id,
                        success=True,
                        task=None,
                        error=None,
                        task_name=result.name,
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
