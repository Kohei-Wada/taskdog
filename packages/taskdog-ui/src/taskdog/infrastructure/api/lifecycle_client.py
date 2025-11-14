"""Task lifecycle operations client."""
# mypy: ignore-errors

from taskdog.infrastructure.api.base_client import BaseApiClient
from taskdog.infrastructure.api.converters import convert_to_task_operation_output
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


class LifecycleClient:
    """Client for task status change operations.

    Operations:
    - Start, complete, pause, cancel, reopen tasks
    - Generic lifecycle operation helper
    """

    def __init__(self, base_client: BaseApiClient):
        """Initialize lifecycle client.

        Args:
            base_client: Base API client for HTTP operations
        """
        self._base = base_client

    def _lifecycle_operation(self, task_id: int, operation: str) -> TaskOperationOutput:
        """Execute a lifecycle operation on a task.

        Generic helper for lifecycle operations (start, complete, pause, cancel, reopen)
        that follow the same pattern.

        Args:
            task_id: Task ID
            operation: Operation name (e.g., "start", "complete", "pause")

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        response = self._base._safe_request(
            "post", f"/api/v1/tasks/{task_id}/{operation}"
        )
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_task_operation_output(data)

    def start_task(self, task_id: int) -> TaskOperationOutput:
        """Start a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "start")

    def complete_task(self, task_id: int) -> TaskOperationOutput:
        """Complete a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "complete")

    def pause_task(self, task_id: int) -> TaskOperationOutput:
        """Pause a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "pause")

    def cancel_task(self, task_id: int) -> TaskOperationOutput:
        """Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "cancel")

    def reopen_task(self, task_id: int) -> TaskOperationOutput:
        """Reopen a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "reopen")
