"""Use case for removing a task."""

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository


class RemoveTaskUseCase(UseCase[SingleTaskInput, None]):
    """Use case for removing tasks."""

    def __init__(self, repository: TaskRepository, notes_repository: NotesRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            notes_repository: Notes repository for notes cleanup
        """
        self.repository = repository
        self.notes_repository = notes_repository

    def execute(self, input_dto: SingleTaskInput) -> None:
        """Execute task removal.

        Deletes both the task and its associated notes file (if any).

        Args:
            input_dto: Task removal input data

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        self._get_task_or_raise(self.repository, input_dto.task_id)

        # Delete notes first (idempotent - won't fail if notes don't exist)
        self.notes_repository.delete_notes(input_dto.task_id)

        # Then delete the task
        self.repository.delete(input_dto.task_id)
