"""Service for dependency graph operations."""

from taskdog_core.domain.repositories.task_repository import TaskRepository


class DependencyGraphService:
    """Service for analyzing and managing task dependency graphs.

    This service provides operations for dependency graph analysis, including
    cycle detection, path finding, and dependency validation.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize service with repository.

        Args:
            repository: Task repository for accessing task data
        """
        self.repository = repository

    def detect_cycle(self, start_task_id: int, target_task_id: int) -> list[int] | None:
        """Detect if adding a dependency would create a cycle using DFS.

        This checks if adding "start_task_id depends on target_task_id" would
        create a cycle by checking if there's already a path from target_task_id
        back to start_task_id.

        Args:
            start_task_id: The task that would depend on target_task_id
            target_task_id: The task to be added as a dependency

        Returns:
            List of task IDs forming the cycle if detected, None otherwise.
            Example: [1, 2, 3, 1] means task1→task2→task3→task1
        """
        visited: set[int] = set()
        rec_stack: list[int] = []

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
