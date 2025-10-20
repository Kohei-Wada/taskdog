"""Use case for adding a task dependency."""

from application.dto.manage_dependencies_request import AddDependencyRequest
from application.services.dependency_graph_service import DependencyGraphService
from application.use_cases.base import UseCase
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskValidationError
from infrastructure.persistence.task_repository import TaskRepository


class AddDependencyUseCase(UseCase[AddDependencyRequest, Task]):
    """Use case for adding a dependency to a task."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository
        self.graph_service = DependencyGraphService(repository)

    def execute(self, input_dto: AddDependencyRequest) -> Task:
        """Execute dependency addition.

        Args:
            input_dto: Dependency addition input data

        Returns:
            Updated task with new dependency

        Raises:
            TaskNotFoundException: If task or dependency doesn't exist
            TaskValidationError: If dependency would create a cycle
        """
        # Get task and validate dependency exists
        task = self._get_task_or_raise(self.repository, input_dto.task_id)
        # Ensure dependency task exists (raises TaskNotFoundException if not)
        self._get_task_or_raise(self.repository, input_dto.depends_on_id)

        # Validate: can't depend on itself
        if input_dto.task_id == input_dto.depends_on_id:
            raise TaskValidationError("Task cannot depend on itself")

        # Validate: dependency not already present
        if input_dto.depends_on_id in task.depends_on:
            raise TaskValidationError(
                f"Task {input_dto.task_id} already depends on task {input_dto.depends_on_id}"
            )

        # Check for circular dependency using DFS
        cycle = self.graph_service.detect_cycle(input_dto.task_id, input_dto.depends_on_id)
        if cycle:
            # Format cycle path for clear error message
            # Prepend start_task_id to show complete cycle (e.g., 3→1→2→3)
            complete_cycle = [input_dto.task_id, *cycle]
            cycle_path = " → ".join(str(tid) for tid in complete_cycle)
            raise TaskValidationError(
                f"Circular dependency detected: adding this dependency would create a cycle:\n"
                f"  {cycle_path}\n"
                f"Task {input_dto.task_id} cannot depend on task {input_dto.depends_on_id} "
                f"because it would create a circular chain."
            )

        # Add dependency
        task.depends_on.append(input_dto.depends_on_id)

        # Save changes
        self.repository.save(task)

        return task
