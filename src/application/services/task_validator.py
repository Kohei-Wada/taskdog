from infrastructure.persistence.task_repository import TaskRepository


class TaskValidator:
    """Validator for task business rules."""

    def validate_parent(
        self, parent_id: int | None, repository: TaskRepository, task_id: int | None = None
    ) -> bool:
        """Validate that parent exists and no circular reference.

        Args:
            parent_id: The ID of the parent task to validate
            repository: Repository to look up tasks
            task_id: The ID of the current task (for circular reference check)

        Returns:
            True if validation passes

        Raises:
            ValueError: If parent doesn't exist or circular reference detected
        """
        if parent_id is None:
            return True

        # Check for self-reference
        if parent_id == task_id:
            raise ValueError("Circular parent reference detected")

        # Check if parent exists
        parent = repository.get_by_id(parent_id)
        if not parent:
            raise ValueError(f"Parent task with ID {parent_id} does not exist")

        # Check for circular reference in ancestor chain
        current = parent
        while current and current.parent_id is not None:
            if current.parent_id == task_id:
                raise ValueError("Circular parent reference detected")
            current = repository.get_by_id(current.parent_id)

        return True
