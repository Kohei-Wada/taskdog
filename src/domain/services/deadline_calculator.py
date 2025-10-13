"""Deadline calculator domain service."""

from domain.entities.task import Task


class DeadlineCalculator:
    """Domain service for calculating effective deadlines.

    Calculates the most restrictive deadline by considering
    a task's own deadline and all ancestor deadlines in the hierarchy.
    """

    @staticmethod
    def get_effective_deadline(task: Task, repository) -> str | None:
        """Calculate effective deadline considering parent task deadlines.

        The effective deadline is the most restrictive (earliest) deadline
        when considering the task's own deadline and all ancestor deadlines.

        Args:
            task: Task to calculate effective deadline for
            repository: Task repository for parent task lookups

        Returns:
            Effective deadline string (YYYY-MM-DD HH:MM:SS) or None if no deadlines exist
        """
        if not repository:
            # If no repository available, use task's own deadline
            return task.deadline

        deadlines = []

        # Add task's own deadline if it exists
        if task.deadline:
            deadlines.append(task.deadline)

        # Traverse up the parent hierarchy with infinite loop protection
        current_task = task
        visited_ids: set[int] = set()
        max_depth = 100  # Safety limit

        while current_task.parent_id and len(visited_ids) < max_depth:
            # Detect circular reference
            if current_task.id in visited_ids:
                break

            if current_task.id is not None:
                visited_ids.add(current_task.id)

            parent = repository.get_by_id(current_task.parent_id)
            if not parent:
                break

            # Add parent's deadline if it exists
            if parent.deadline:
                deadlines.append(parent.deadline)

            current_task = parent

        # Return the earliest (most restrictive) deadline
        if deadlines:
            return min(deadlines)

        return None
