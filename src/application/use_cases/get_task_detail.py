"""Use case for getting task detail with notes."""

from application.dto.task_detail_result import GetTaskDetailResult
from application.use_cases.base import UseCase
from infrastructure.persistence.task_repository import TaskRepository


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

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

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

        # Check if notes file exists and read content
        notes_path = task.notes_path
        notes_content: str | None = None
        has_notes = False

        if notes_path.exists():
            try:
                notes_content = notes_path.read_text(encoding="utf-8")
                has_notes = True
            except (OSError, UnicodeDecodeError):
                # If reading fails (file permissions, encoding issues, etc.),
                # treat as no notes to maintain user experience.
                # In production, consider logging the error for debugging.
                pass

        return GetTaskDetailResult(task=task, notes_content=notes_content, has_notes=has_notes)
