"""Use case for creating a task."""

from application.dto.create_task_input import CreateTaskInput
from application.use_cases.base import UseCase
from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository


class CreateTaskUseCase(UseCase[CreateTaskInput, Task]):
    """Use case for creating a new task with auto-generated ID."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: CreateTaskInput) -> Task:
        """Execute task creation.

        Args:
            input_dto: Task creation input data

        Returns:
            Created task with ID assigned
        """
        # Create task via repository (ID auto-assigned)
        task = self.repository.create(
            name=input_dto.name,
            priority=input_dto.priority,
            planned_start=input_dto.planned_start,
            planned_end=input_dto.planned_end,
            deadline=input_dto.deadline,
            estimated_duration=input_dto.estimated_duration,
            is_fixed=input_dto.is_fixed,
        )

        return task
