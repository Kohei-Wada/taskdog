"""Use case for getting task detail with notes."""

from taskdog_core.application.dto.task_detail_output import GetTaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.entities.task import Task
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


class GetTaskDetailUseCase(UseCase[GetTaskDetailInput, GetTaskDetailOutput]):
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

    def execute(self, input_dto: GetTaskDetailInput) -> GetTaskDetailOutput:
        """Execute task detail retrieval.

        Args:
            input_dto: Input data containing task ID

        Returns:
            GetTaskDetailOutput with task and notes information

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Use NotesRepository to check and read notes
        has_notes = self.notes_repository.has_notes(input_dto.task_id)
        notes_content = (
            self.notes_repository.read_notes(input_dto.task_id) if has_notes else None
        )

        # Convert Task entity to DTO
        task_dto = self._convert_to_dto(task)

        return GetTaskDetailOutput(
            task=task_dto, notes_content=notes_content, has_notes=has_notes
        )

    def _convert_to_dto(self, task: Task) -> TaskDetailDto:
        """Convert Task entity to TaskDetailDto.

        Args:
            task: Task entity

        Returns:
            TaskDetailDto with all task data
        """
        # Tasks from repository must have an ID
        if task.id is None:
            raise ValueError("Task must have an ID")

        return TaskDetailDto(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            estimated_duration=task.estimated_duration,
            daily_allocations=task.daily_allocations,
            is_fixed=task.is_fixed,
            depends_on=task.depends_on,
            actual_daily_hours=task.actual_daily_hours,
            tags=task.tags,
            is_archived=task.is_archived,
            created_at=task.created_at,
            updated_at=task.updated_at,
            actual_duration_hours=task.actual_duration_hours,
            is_active=task.is_active,
            is_finished=task.is_finished,
            can_be_modified=task.can_be_modified,
            is_schedulable=task.is_schedulable(force_override=False),
        )
