"""Task relationship operations client."""

from taskdog.infrastructure.api.base_client import BaseApiClient
from taskdog.infrastructure.api.converters import convert_to_task_operation_output
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


class RelationshipClient:
    """Client for task relationships (dependencies, tags, hours).

    Operations:
    - Add/remove dependencies
    - Set tags
    - Log work hours
    """

    def __init__(self, base_client: BaseApiClient):
        """Initialize relationship client.

        Args:
            base_client: Base API client for HTTP operations
        """
        self._base = base_client

    def add_dependency(self, task_id: int, depends_on_id: int) -> TaskOperationOutput:
        """Add a dependency to a task.

        Args:
            task_id: Task ID
            depends_on_id: ID of task to depend on

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails (e.g., circular dependency)
        """
        response = self._base._safe_request(
            "post",
            f"/api/v1/tasks/{task_id}/dependencies",
            json={"depends_on_id": depends_on_id},
        )
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_task_operation_output(data)

    def remove_dependency(
        self, task_id: int, depends_on_id: int
    ) -> TaskOperationOutput:
        """Remove a dependency from a task.

        Args:
            task_id: Task ID
            depends_on_id: Dependency ID to remove

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        response = self._base._safe_request(
            "delete", f"/api/v1/tasks/{task_id}/dependencies/{depends_on_id}"
        )
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_task_operation_output(data)

    def set_task_tags(self, task_id: int, tags: list[str]) -> TaskOperationOutput:
        """Set task tags (replaces existing tags).

        Args:
            task_id: Task ID
            tags: New tags list

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        response = self._base._safe_request(
            "put", f"/api/v1/tasks/{task_id}/tags", json={"tags": tags}
        )
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_task_operation_output(data)

    def log_hours(
        self, task_id: int, hours: float, date_str: str
    ) -> TaskOperationOutput:
        """Log actual hours worked on a task.

        Args:
            task_id: Task ID
            hours: Hours worked
            date_str: Date in ISO format

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        response = self._base._safe_request(
            "post",
            f"/api/v1/tasks/{task_id}/log-hours",
            json={"hours": hours, "date": date_str},
        )
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_task_operation_output(data)
