"""Notes controller for orchestrating task notes operations.

This controller provides a consistent interface for notes CRUD operations,
with task existence validation. Presentation layers (API server) should use
this controller rather than accessing the notes repository directly.
"""

from taskdog_core.application.dto.notes_output import NotesOutput
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository


class NotesController:
    """Controller for task notes operations.

    Validates task existence before performing notes operations,
    ensuring consistent error handling across all endpoints.

    Attributes:
        _repository: Task repository for existence validation
        _notes_repository: Notes repository for notes persistence
    """

    def __init__(
        self,
        repository: TaskRepository,
        notes_repository: NotesRepository,
    ) -> None:
        """Initialize the notes controller.

        Args:
            repository: Task repository for existence validation
            notes_repository: Notes repository for notes persistence
        """
        self._repository = repository
        self._notes_repository = notes_repository

    def _get_task_or_raise(self, task_id: int) -> str:
        """Verify task exists and return its name.

        Args:
            task_id: Task ID to verify

        Returns:
            Task name

        Raises:
            TaskNotFoundException: If task does not exist
        """
        task = self._repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)
        return task.name

    def get_notes(self, task_id: int) -> NotesOutput:
        """Get notes for a task.

        Args:
            task_id: Task ID

        Returns:
            NotesOutput with content and metadata

        Raises:
            TaskNotFoundException: If task does not exist
        """
        task_name = self._get_task_or_raise(task_id)
        has_notes = self._notes_repository.has_notes(task_id)
        content = self._notes_repository.read_notes(task_id) or ""
        return NotesOutput(
            task_id=task_id,
            task_name=task_name,
            content=content,
            has_notes=has_notes,
        )

    def update_notes(self, task_id: int, content: str) -> NotesOutput:
        """Update notes for a task.

        Args:
            task_id: Task ID
            content: New notes content (markdown)

        Returns:
            NotesOutput with updated content and metadata

        Raises:
            TaskNotFoundException: If task does not exist
        """
        task_name = self._get_task_or_raise(task_id)
        self._notes_repository.write_notes(task_id, content)
        has_notes = self._notes_repository.has_notes(task_id)
        return NotesOutput(
            task_id=task_id,
            task_name=task_name,
            content=content,
            has_notes=has_notes,
        )

    def delete_notes(self, task_id: int) -> NotesOutput:
        """Delete notes for a task.

        Args:
            task_id: Task ID

        Returns:
            NotesOutput with task info (for broadcast/audit)

        Raises:
            TaskNotFoundException: If task does not exist
        """
        task_name = self._get_task_or_raise(task_id)
        self._notes_repository.write_notes(task_id, "")
        return NotesOutput(
            task_id=task_id,
            task_name=task_name,
            content="",
            has_notes=False,
        )
