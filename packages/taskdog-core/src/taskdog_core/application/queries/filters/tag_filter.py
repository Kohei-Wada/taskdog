"""Filter for tasks by tags."""

from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import Task


class TagFilter(TaskFilter):
    """Filter tasks by tags.

    Supports both AND and OR logic for tag matching.
    """

    def __init__(self, tags: list[str], match_all: bool = False):
        """Initialize filter with target tags.

        Args:
            tags: List of tags to filter by
            match_all: If True, task must have all tags (AND logic).
                      If False, task must have at least one tag (OR logic).
        """
        self.tags = tags
        self.match_all = match_all

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks by tags.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks matching the tag filter
        """
        if not self.tags:
            return tasks

        if self.match_all:
            # AND logic: task must have all specified tags
            return [
                task for task in tasks if all(tag in task.tags for tag in self.tags)
            ]
        else:
            # OR logic: task must have at least one specified tag
            return [
                task for task in tasks if any(tag in task.tags for tag in self.tags)
            ]
