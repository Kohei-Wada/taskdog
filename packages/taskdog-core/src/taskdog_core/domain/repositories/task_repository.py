from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from taskdog_core.domain.entities.task import Task, TaskStatus


class TaskRepository(ABC):
    """Abstract interface for task data persistence."""

    @abstractmethod
    def get_all(self) -> list[Task]:
        """Retrieve all tasks.

        Returns:
            List of all tasks
        """
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task | None:
        """Retrieve a task by its ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        pass

    @abstractmethod
    def get_by_ids(self, task_ids: list[int]) -> dict[int, Task]:
        """Retrieve multiple tasks by their IDs in a single operation.

        Args:
            task_ids: List of task IDs to retrieve

        Returns:
            Dictionary mapping task IDs to Task objects.
            Missing IDs are not included in the result.

        Notes:
            - More efficient than multiple get_by_id() calls
            - Prevents N+1 query problems in database implementations
            - O(n) time complexity where n is len(task_ids)
        """
        pass

    def get_filtered(
        self,
        include_archived: bool = True,
        status: TaskStatus | None = None,
        tags: list[str] | None = None,
        match_all_tags: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Task]:
        """Retrieve tasks with SQL WHERE clauses for efficient filtering.

        This is an optional optimization method. Repositories that don't override
        this method will fall back to fetching all tasks and filtering in Python.

        Args:
            include_archived: If False, exclude archived tasks (default: True)
            status: Filter by task status (default: None, no status filter)
            tags: Filter by tags with OR logic (default: None, no tag filter)
            match_all_tags: If True, require all tags (AND); if False, any tag (OR)
            start_date: Filter tasks with any date >= start_date (default: None)
            end_date: Filter tasks with any date <= end_date (default: None)

        Returns:
            List of tasks matching the filter criteria

        Notes:
            - Default implementation falls back to get_all() (no optimization)
            - Repositories should override this for SQL-level filtering
            - Date filtering typically checks multiple date fields (deadline, planned dates, etc.)
        """
        # Default implementation: fallback to get_all() without optimization
        # Subclasses should override this method to provide SQL-level filtering
        return self.get_all()

    @abstractmethod
    def save(self, task: Task) -> None:
        """Save a task (create new or update existing).

        Args:
            task: The task to save
        """
        pass

    @abstractmethod
    def save_all(self, tasks: list[Task]) -> None:
        """Save multiple tasks in a single transaction.

        Args:
            tasks: List of tasks to save

        Notes:
            - All saves succeed or all fail (atomicity)
            - More efficient than multiple save() calls
            - Implementation-specific optimization possible
        """
        pass

    @abstractmethod
    def delete(self, task_id: int) -> None:
        """Delete a task by its ID.

        Args:
            task_id: The ID of the task to delete
        """
        pass

    @abstractmethod
    def generate_next_id(self) -> int:
        """Generate the next available task ID.

        Returns:
            The next available ID
        """
        pass

    @abstractmethod
    def create(self, name: str, priority: int, **kwargs: Any) -> Task:
        """Create a new task with auto-generated ID and save it.

        Args:
            name: Task name
            priority: Task priority
            **kwargs: Additional task fields

        Returns:
            Created task with ID assigned
        """
        pass

    @abstractmethod
    def reload(self) -> None:
        """Reload tasks from the data source.

        This method refreshes the in-memory cache from the underlying data source,
        allowing detection of changes made by external processes.
        """
        pass
