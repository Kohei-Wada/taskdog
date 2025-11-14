"""Task notes operations client."""
# mypy: ignore-errors

from taskdog.infrastructure.api.base_client import BaseApiClient


class NotesClient:
    """Client for task notes operations with caching.

    Operations:
    - Get, update, delete notes
    - Check note existence (with cache)
    - Cache management
    """

    def __init__(self, base_client: BaseApiClient):
        """Initialize notes client.

        Args:
            base_client: Base API client for HTTP operations
        """
        self._base = base_client
        self._has_notes_cache: dict[int, bool] = {}

    def get_task_notes(self, task_id: int) -> tuple[str, bool]:
        """Get task notes.

        Args:
            task_id: Task ID

        Returns:
            Tuple of (notes_content, has_notes)

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._base._safe_request("get", f"/api/v1/tasks/{task_id}/notes")
        if response.status_code != 200:
            self._base._handle_error(response)
        data = response.json()
        return data["content"], data["has_notes"]

    def update_task_notes(self, task_id: int, content: str) -> None:
        """Update task notes.

        Args:
            task_id: Task ID
            content: Notes content (markdown)

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._base._safe_request(
            "put", f"/api/v1/tasks/{task_id}/notes", json={"content": content}
        )
        if response.status_code != 200:
            self._base._handle_error(response)

    def delete_task_notes(self, task_id: int) -> None:
        """Delete task notes.

        Args:
            task_id: Task ID

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._base._safe_request("delete", f"/api/v1/tasks/{task_id}/notes")
        if response.status_code != 204:
            self._base._handle_error(response)

    def has_task_notes(self, task_id: int) -> bool:
        """Check if task has notes.

        Uses cached information from list_tasks if available, otherwise queries API.

        Args:
            task_id: Task ID

        Returns:
            True if task has notes, False otherwise

        Raises:
            TaskNotFoundException: If task not found
        """
        # Use cache if available (populated by list_tasks)
        if task_id in self._has_notes_cache:
            return self._has_notes_cache[task_id]

        # Fall back to API call
        _, has_notes = self.get_task_notes(task_id)
        self._has_notes_cache[task_id] = has_notes
        return has_notes

    def cache_notes_info(self, task_id: int, has_notes: bool) -> None:
        """Cache has_notes information for a task.

        Args:
            task_id: Task ID
            has_notes: Whether task has notes
        """
        self._has_notes_cache[task_id] = has_notes

    def clear_cache(self) -> None:
        """Clear the has_notes cache."""
        self._has_notes_cache.clear()
