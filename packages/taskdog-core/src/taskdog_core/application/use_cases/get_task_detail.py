"""Use case for getting task detail with notes."""

from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository


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


class GetTaskDetailUseCase(UseCase[GetTaskDetailInput, TaskDetailOutput]):
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

    def execute(self, input_dto: GetTaskDetailInput) -> TaskDetailOutput:
        """Execute task detail retrieval.

        Args:
            input_dto: Input data containing task ID

        Returns:
            TaskDetailOutput with task and notes information

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Read notes in a single query (read_notes returns None if no notes exist)
        notes_content = self.notes_repository.read_notes(input_dto.task_id)
        has_notes = notes_content is not None

        # Convert Task entity to DTO
        task_dto = TaskDetailDto.from_entity(task)

        return TaskDetailOutput(
            task=task_dto, notes_content=notes_content, has_notes=has_notes
        )
