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

    def _detect_cycle(self, start_task_id: int, target_task_id: int) -> list[int] | None:
        """Detect if adding a dependency would create a cycle using DFS.

        This checks if adding "start_task_id depends on target_task_id" would
        create a cycle by checking if there's already a path from target_task_id
        back to start_task_id.

        Args:
            start_task_id: The task that would depend on target_task_id
            target_task_id: The task to be added as a dependency

        Returns:
            List of task IDs forming the cycle if detected, None otherwise
            Example: [1, 2, 3, 1] means task1→task2→task3→task1
        """
        visited = set()
        rec_stack = []

        def dfs(current_id: int) -> bool:
            """Depth-first search to detect if we can reach start_task_id.

            Args:
                current_id: Current task ID being explored

            Returns:
                True if we can reach start_task_id, False otherwise
            """
            # If we reached the start task, we found a cycle
            if current_id == start_task_id:
                rec_stack.append(current_id)
                return True

            # If already visited in this path, no cycle here
            if current_id in visited:
                return False

            visited.add(current_id)
            rec_stack.append(current_id)

            # Get current task's dependencies
            current_task = self.repository.get_by_id(current_id)
            if current_task and current_task.depends_on:
                for dep_id in current_task.depends_on:
                    if dfs(dep_id):
                        return True

            rec_stack.pop()
            return False

        # Start DFS from the target task
        # If we can reach start_task from target_task, adding the dependency creates a cycle
        if dfs(target_task_id):
            return rec_stack.copy()

        return None

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

        # Check for circular dependency using DFS
        cycle = self._detect_cycle(input_dto.task_id, input_dto.depends_on_id)
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
