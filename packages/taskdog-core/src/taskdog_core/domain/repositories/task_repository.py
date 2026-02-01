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

    def count_tasks(
        self,
        include_archived: bool = True,
        status: TaskStatus | None = None,
        tags: list[str] | None = None,
        match_all_tags: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:
        """Count tasks matching filter criteria with SQL COUNT for efficiency.

        This is an optional optimization method. Repositories that don't override
        this method will fall back to counting tasks in Python.

        Args:
            include_archived: If False, exclude archived tasks (default: True)
            status: Filter by task status (default: None, no status filter)
            tags: Filter by tags (default: None, no tag filter)
            match_all_tags: If True, require all tags (AND); if False, any tag (OR)
            start_date: Filter tasks with any date >= start_date (default: None)
            end_date: Filter tasks with any date <= end_date (default: None)

        Returns:
            Number of tasks matching the filter criteria

        Notes:
            - Default implementation uses len(get_filtered()) (no optimization)
            - Repositories should override this for SQL COUNT optimization
            - Uses same filter logic as get_filtered() for consistency
        """
        # Default implementation: fallback to counting filtered tasks
        # Subclasses should override this method to use SQL COUNT
        return len(
            self.get_filtered(
                include_archived, status, tags, match_all_tags, start_date, end_date
            )
        )

    def count_tasks_with_tags(self) -> int:
        """Count tasks that have at least one tag.

        This is an optional optimization method. Repositories that don't override
        this method will fall back to counting in Python.

        Returns:
            Number of tasks with at least one tag

        Notes:
            - Default implementation iterates all tasks (no optimization)
            - Repositories should override this for SQL COUNT optimization
            - Useful for tag statistics without loading all tasks
        """
        # Default implementation: fallback to Python iteration
        # Subclasses should override this method to use SQL COUNT
        return sum(1 for task in self.get_all() if task.tags)

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
    def create(self, name: str, priority: int | None = None, **kwargs: Any) -> Task:
        """Create a new task with auto-generated ID and save it.

        Args:
            name: Task name
            priority: Task priority (optional, can be None)
            **kwargs: Additional task fields

        Returns:
            Created task with ID assigned
        """
        pass

    def get_daily_workload_totals(
        self,
        start_date: date,
        end_date: date,
        task_ids: list[int] | None = None,
    ) -> dict[date, float]:
        """Get daily workload totals using SQL aggregation.

        This method uses SQL SUM/GROUP BY on the daily_allocations table for
        efficient workload calculation, avoiding Python loops.

        Args:
            start_date: Start date of the calculation period
            end_date: End date of the calculation period
            task_ids: Optional list of task IDs to include. If None, includes all tasks.

        Returns:
            Dictionary mapping date to total hours {date: hours}

        Notes:
            - Default implementation falls back to empty dict (no optimization)
            - Repositories should override this for SQL-level aggregation
            - Only includes dates with non-zero hours
        """
        # Default implementation: fallback to empty dict (no optimization)
        # Subclasses should override this method to use SQL aggregation
        return {}

    def get_daily_allocations_for_tasks(
        self,
        task_ids: list[int],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[int, dict[date, float]]:
        """Get daily allocations for multiple tasks in a single query.

        This method uses SQL to fetch daily allocations for multiple tasks
        efficiently, avoiding N+1 query problems.

        Args:
            task_ids: List of task IDs to fetch allocations for
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)

        Returns:
            Dictionary mapping task_id to {date: hours} allocations

        Notes:
            - Default implementation returns empty dict (no optimization)
            - Repositories should override this for SQL-level fetching
            - More efficient than loading full Task entities when only
              allocations are needed
        """
        # Default implementation: fallback to empty dict (no optimization)
        # Subclasses should override this method to use SQL fetching
        return {}
