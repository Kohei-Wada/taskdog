"""Task CRUD operations client."""

from datetime import datetime
from typing import Any

from taskdog_client.base_client import BaseApiClient
from taskdog_client.converters import (
    convert_to_task_operation_output,
    convert_to_update_task_output,
)
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.domain.entities.task import TaskStatus


class TaskClient:
    """Client for task CRUD operations.

    Operations:
    - Create, update, archive, restore, delete tasks
    - Payload building helpers
    """

    def __init__(self, base_client: BaseApiClient):
        """Initialize task client.

        Args:
            base_client: Base API client for HTTP operations
        """
        self._base = base_client

    def create_task(
        self,
        name: str,
        priority: int | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        is_fixed: bool = False,
        tags: list[str] | None = None,
    ) -> TaskOperationOutput:
        """Create a new task.

        Args:
            name: Task name
            priority: Task priority
            deadline: Task deadline
            estimated_duration: Estimated duration in hours
            planned_start: Planned start datetime
            planned_end: Planned end datetime
            is_fixed: Whether schedule is fixed
            tags: List of tags

        Returns:
            TaskOperationOutput with created task data

        Raises:
            TaskValidationError: If validation fails
        """
        payload = {
            "name": name,
            "priority": priority,
            "deadline": deadline.isoformat() if deadline else None,
            "estimated_duration": estimated_duration,
            "planned_start": planned_start.isoformat() if planned_start else None,
            "planned_end": planned_end.isoformat() if planned_end else None,
            "is_fixed": is_fixed,
            "tags": tags,
        }

        data = self._base._request_json("post", "/api/v1/tasks", json=payload)
        return convert_to_task_operation_output(data)

    def _build_update_payload(
        self,
        name: str | None,
        priority: int | None,
        status: TaskStatus | None,
        planned_start: datetime | None,
        planned_end: datetime | None,
        deadline: datetime | None,
        estimated_duration: float | None,
        is_fixed: bool | None,
        tags: list[str] | None,
    ) -> dict[str, Any]:
        """Build update task payload from optional parameters.

        Args:
            name: New task name
            priority: New priority
            status: New status
            planned_start: New planned start
            planned_end: New planned end
            deadline: New deadline
            estimated_duration: New estimated duration
            is_fixed: New fixed status
            tags: New tags list

        Returns:
            Dictionary with non-None fields
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if priority is not None:
            payload["priority"] = priority
        if status is not None:
            payload["status"] = status.value
        if planned_start is not None:
            payload["planned_start"] = planned_start.isoformat()
        if planned_end is not None:
            payload["planned_end"] = planned_end.isoformat()
        if deadline is not None:
            payload["deadline"] = deadline.isoformat()
        if estimated_duration is not None:
            payload["estimated_duration"] = estimated_duration
        if is_fixed is not None:
            payload["is_fixed"] = is_fixed
        if tags is not None:
            payload["tags"] = tags
        return payload

    def update_task(
        self,
        task_id: int,
        name: str | None = None,
        priority: int | None = None,
        status: TaskStatus | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        is_fixed: bool | None = None,
        tags: list[str] | None = None,
    ) -> TaskUpdateOutput:
        """Update task fields.

        Args:
            task_id: Task ID
            name: New task name
            priority: New priority
            status: New status
            planned_start: New planned start
            planned_end: New planned end
            deadline: New deadline
            estimated_duration: New estimated duration
            is_fixed: New fixed status
            tags: New tags list

        Returns:
            TaskUpdateOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        payload = self._build_update_payload(
            name,
            priority,
            status,
            planned_start,
            planned_end,
            deadline,
            estimated_duration,
            is_fixed,
            tags,
        )

        data = self._base._request_json(
            "patch", f"/api/v1/tasks/{task_id}", json=payload
        )
        return convert_to_update_task_output(data)

    def _lifecycle_operation(self, task_id: int, operation: str) -> TaskOperationOutput:
        """Execute a lifecycle operation on a task.

        Generic helper for lifecycle operations (archive, restore)
        that follow the same pattern.

        Args:
            task_id: Task ID
            operation: Operation name (e.g., "archive", "restore")

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        data = self._base._request_json("post", f"/api/v1/tasks/{task_id}/{operation}")
        return convert_to_task_operation_output(data)

    def archive_task(self, task_id: int) -> TaskOperationOutput:
        """Archive (soft delete) a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with archived task data

        Raises:
            TaskNotFoundException: If task not found
        """
        return self._lifecycle_operation(task_id, "archive")

    def restore_task(self, task_id: int) -> TaskOperationOutput:
        """Restore an archived task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with restored task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If not archived
        """
        return self._lifecycle_operation(task_id, "restore")

    def remove_task(self, task_id: int) -> None:
        """Permanently delete a task.

        Args:
            task_id: Task ID

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._base._safe_request("delete", f"/api/v1/tasks/{task_id}")
        if not response.is_success:
            self._base._handle_error(response)
