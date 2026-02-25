"""Task notes operations client."""

from taskdog_client.base_client import BaseApiClient


class NotesClient:
    """Client for task notes operations.

    Operations:
    - Get, update, delete notes
    """

    def __init__(self, base_client: BaseApiClient):
        """Initialize notes client.

        Args:
            base_client: Base API client for HTTP operations
        """
        self._base = base_client

    def get_task_notes(self, task_id: int) -> tuple[str, bool]:
        """Get task notes.

        Args:
            task_id: Task ID

        Returns:
            Tuple of (notes_content, has_notes)

        Raises:
            TaskNotFoundException: If task not found
        """
        data = self._base._request_json("get", f"/api/v1/tasks/{task_id}/notes")
        return data["content"], data["has_notes"]

    def update_task_notes(self, task_id: int, content: str) -> None:
        """Update task notes.

        Args:
            task_id: Task ID
            content: Notes content (markdown)

        Raises:
            TaskNotFoundException: If task not found
        """
        self._base._request_json(
            "put", f"/api/v1/tasks/{task_id}/notes", json={"content": content}
        )

    def delete_task_notes(self, task_id: int) -> None:
        """Delete task notes.

        Args:
            task_id: Task ID

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._base._safe_request("delete", f"/api/v1/tasks/{task_id}/notes")
        if not response.is_success:
            self._base._handle_error(response)
