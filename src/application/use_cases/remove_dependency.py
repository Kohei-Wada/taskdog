"""Use case for removing a task dependency."""

from application.dto.manage_dependencies_input import RemoveDependencyInput
from application.use_cases.base import UseCase
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskValidationError
from infrastructure.persistence.task_repository import TaskRepository


class RemoveDependencyUseCase(UseCase[RemoveDependencyInput, Task]):
    """Use case for removing a dependency from a task."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: RemoveDependencyInput) -> Task:
        """Execute dependency removal.

        Args:
            input_dto: Dependency removal input data

        Returns:
            Updated task with dependency removed

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskValidationError: If dependency doesn't exist on task
        """
        # Get task
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Validate: dependency exists
        if input_dto.depends_on_id not in task.depends_on:
            raise TaskValidationError(
                f"Task {input_dto.task_id} does not depend on task {input_dto.depends_on_id}"
            )

        # Remove dependency
        task.depends_on.remove(input_dto.depends_on_id)

        # Save changes
        self.repository.save(task)

        return task
