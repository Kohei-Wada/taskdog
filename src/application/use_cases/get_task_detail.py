"""Use case for getting task detail with notes."""

from application.dto.task_detail_result import GetTaskDetailResult
from application.use_cases.base import UseCase
from domain.repositories.notes_repository import NotesRepository
from domain.repositories.task_repository import TaskRepository


class GetTaskDetailInput:
    """Input for getting task detail.

    Attributes:
        task_id: ID of the task to retrieve
    """

    def __init__(self, task_id: int):
        """Initialize input.

        Args:
            task_id: ID of the task to retrieve
        """
        self.task_id = task_id


class GetTaskDetailUseCase(UseCase[GetTaskDetailInput, GetTaskDetailResult]):
    """Use case for retrieving task details with notes.

    This use case fetches a task by ID and its associated notes file
    if it exists, returning them as a unified DTO.
    """

    def __init__(self, repository: TaskRepository, notes_repository: NotesRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            notes_repository: Notes repository for notes file access
        """
        self.repository = repository
        self.notes_repository = notes_repository

    def execute(self, input_dto: GetTaskDetailInput) -> GetTaskDetailResult:
        """Execute task detail retrieval.

        Args:
            input_dto: Input data containing task ID

        Returns:
            GetTaskDetailResult with task and notes information

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Use NotesRepository to check and read notes
        has_notes = self.notes_repository.has_notes(input_dto.task_id)
        notes_content = self.notes_repository.read_notes(input_dto.task_id) if has_notes else None

        return GetTaskDetailResult(task=task, notes_content=notes_content, has_notes=has_notes)
