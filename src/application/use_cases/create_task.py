"""Use case for creating a task."""

from application.dto.create_task_input import CreateTaskInput
from application.services.hierarchy_manager import HierarchyManager
from application.use_cases.base import UseCase
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskNotFoundException
from infrastructure.persistence.task_repository import TaskRepository


class CreateTaskUseCase(UseCase[CreateTaskInput, Task]):
    """Use case for creating a new task.

    Validates parent existence and creates task with auto-generated ID.
    When a child task is created, automatically updates parent's estimated_duration.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize use case with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository
        self.hierarchy_manager = HierarchyManager(repository)

    def execute(self, input_dto: CreateTaskInput) -> Task:
        """Execute task creation.

        Args:
            input_dto: Task creation input data

        Returns:
            Created task with ID assigned

        Raises:
            TaskNotFoundException: If parent_id specified but parent doesn't exist
        """
        # Validate parent if specified
        if input_dto.parent_id is not None:
            parent = self.repository.get_by_id(input_dto.parent_id)
            if not parent:
                raise TaskNotFoundException(input_dto.parent_id)

        # Create task via repository (ID auto-assigned)
        task = self.repository.create(
            name=input_dto.name,
            priority=input_dto.priority,
            parent_id=input_dto.parent_id,
            planned_start=input_dto.planned_start,
            planned_end=input_dto.planned_end,
            deadline=input_dto.deadline,
            estimated_duration=input_dto.estimated_duration,
        )

        # Update parent's estimated_duration if child task has a parent
        if task.parent_id is not None:
            self.hierarchy_manager.update_parent_estimated_duration(task.parent_id)

        return task
