"""Service for handling operations on hierarchical task structures."""

from collections.abc import Callable

from infrastructure.persistence.task_repository import TaskRepository


class HierarchyOperationService:
    """Unified handler for operations on hierarchical tasks.

    This service provides common patterns for operating on task hierarchies:
    - Cascade mode: Recursively apply operation to task and all descendants
    - Orphan mode: Detach children from parent, then apply operation to parent

    The operation itself is provided as a callback, allowing this service
    to be reused for different operations (delete, archive, etc.).
    """

    def execute_cascade(
        self,
        task_id: int,
        repository: TaskRepository,
        operation: Callable[[int], None],
    ) -> int:
        """Recursively apply operation to task and all descendants.

        Processes children first (depth-first), then applies operation to parent.
        This ensures referential integrity when deleting or modifying hierarchies.

        Args:
            task_id: ID of the task to process
            repository: Task repository for data access
            operation: Function to apply to each task ID (e.g., delete or archive)

        Returns:
            Number of tasks processed

        Example:
            >>> service = HierarchyOperationService()
            >>> count = service.execute_cascade(
            ...     task_id=1,
            ...     repository=repo,
            ...     operation=lambda tid: repo.delete(tid)
            ... )
        """
        processed_count = 0

        # Recursively process all children first
        children = repository.get_children(task_id)
        for child in children:
            assert child.id is not None  # Children from repository always have IDs
            processed_count += self.execute_cascade(child.id, repository, operation)

        # Apply operation to the task itself
        operation(task_id)
        processed_count += 1

        return processed_count

    def execute_orphan(
        self,
        task_id: int,
        repository: TaskRepository,
        operation: Callable[[int], None],
    ) -> int:
        """Orphan children and apply operation to parent task.

        Sets all children's parent_id to None before applying the operation.
        This preserves child tasks while removing/modifying the parent.

        Args:
            task_id: ID of the task to process
            repository: Task repository for data access
            operation: Function to apply to the task ID (e.g., delete or archive)

        Returns:
            Number of tasks processed (always 1)

        Example:
            >>> service = HierarchyOperationService()
            >>> count = service.execute_orphan(
            ...     task_id=1,
            ...     repository=repo,
            ...     operation=lambda tid: repo.delete(tid)
            ... )
        """
        # Orphan children (set their parent_id to None)
        children = repository.get_children(task_id)
        for child in children:
            child.parent_id = None
            repository.save(child)

        # Apply operation to the task itself
        operation(task_id)

        return 1
