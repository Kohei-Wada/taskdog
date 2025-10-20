"""Use case for adding a task dependency."""

from application.dto.manage_dependencies_input import AddDependencyInput
from application.use_cases.base import UseCase
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from infrastructure.persistence.task_repository import TaskRepository


class AddDependencyUseCase(UseCase[AddDependencyInput, Task]):
    """Use case for adding a dependency to a task."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: AddDependencyInput) -> Task:
        """Execute dependency addition.

        Args:
            input_dto: Dependency addition input data

        Returns:
            Updated task with new dependency

        Raises:
            TaskNotFoundException: If task or dependency doesn't exist
            TaskValidationError: If dependency would create a cycle
        """
        # Get both tasks
        task = self.repository.get_by_id(input_dto.task_id)
        if task is None:
            raise TaskNotFoundException(input_dto.task_id)

        dependency = self.repository.get_by_id(input_dto.depends_on_id)
        if dependency is None:
            raise TaskNotFoundException(input_dto.depends_on_id)

        # Validate: can't depend on itself
        if input_dto.task_id == input_dto.depends_on_id:
            raise TaskValidationError("Task cannot depend on itself")

        # Validate: dependency not already present
        if input_dto.depends_on_id in task.depends_on:
            raise TaskValidationError(
                f"Task {input_dto.task_id} already depends on task {input_dto.depends_on_id}"
            )

        # Check for circular dependency (simple check: B depends on A, can't add A depends on B)
        if task.id in dependency.depends_on:
            raise TaskValidationError(
                f"Circular dependency detected: task {input_dto.depends_on_id} "
                f"already depends on task {input_dto.task_id}"
            )

        # Add dependency
        task.depends_on.append(input_dto.depends_on_id)

        # Save changes
        self.repository.save(task)

        return task
