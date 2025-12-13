"""Task lifecycle operations client."""

from datetime import datetime

from taskdog_client.base_client import BaseApiClient
from taskdog_client.converters import convert_to_task_operation_output
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
        data = self._base._request_json("post", f"/api/v1/tasks/{task_id}/{operation}")
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

    def fix_actual_times(
        self,
        task_id: int,
        actual_start: datetime | None = None,
        actual_end: datetime | None = None,
        actual_duration: float | None = None,
        clear_start: bool = False,
        clear_end: bool = False,
        clear_duration: bool = False,
    ) -> TaskOperationOutput:
        """Fix actual start/end timestamps and/or duration for a task.

        Used to correct timestamps after the fact, for historical accuracy.
        Past dates are allowed since these are historical records.

        Args:
            task_id: Task ID
            actual_start: New actual start datetime
            actual_end: New actual end datetime
            actual_duration: Explicit duration in hours (overrides calculated value)
            clear_start: Clear actual_start timestamp
            clear_end: Clear actual_end timestamp
            clear_duration: Clear actual_duration (use calculated value)

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        payload: dict[str, object] = {
            "clear_start": clear_start,
            "clear_end": clear_end,
            "clear_duration": clear_duration,
        }
        if actual_start is not None:
            payload["actual_start"] = actual_start.isoformat()
        if actual_end is not None:
            payload["actual_end"] = actual_end.isoformat()
        if actual_duration is not None:
            payload["actual_duration"] = actual_duration

        data = self._base._request_json(
            "post",
            f"/api/v1/tasks/{task_id}/fix-actual",
            json=payload,
        )
        return convert_to_task_operation_output(data)
