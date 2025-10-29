"""Task index manager for O(1) task lookups.

This module provides efficient task indexing for fast retrieval by ID.
Maintains two indexes:
- task_index: Maps task IDs to Task objects
- task_position: Maps task IDs to their position in the task list
"""

from domain.entities.task import Task


class TaskIndexManager:
    """Manages in-memory indexes for fast task lookups.

    Provides O(1) access to tasks by ID using two complementary indexes:
    1. task_index: Direct access to Task objects
    2. task_position: Access to position in task list for updates/deletions
    """

    def __init__(self, tasks: list[Task] | None = None):
        """Initialize the index manager.

        Args:
            tasks: Optional initial list of tasks to index
        """
        self._task_index: dict[int, Task] = {}
        self._task_position: dict[int, int] = {}
        if tasks:
            self.build_indexes(tasks)

    def build_indexes(self, tasks: list[Task]) -> None:
        """Build both indexes from a list of tasks.

        Args:
            tasks: List of tasks to index
        """
        self._task_index = {task.id: task for task in tasks if task.id is not None}
        self._task_position = {task.id: i for i, task in enumerate(tasks) if task.id is not None}

    def get_by_id(self, task_id: int) -> Task | None:
        """Retrieve a task by its ID in O(1) time.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        return self._task_index.get(task_id)

    def get_by_ids(self, task_ids: list[int]) -> dict[int, Task]:
        """Retrieve multiple tasks by their IDs in O(n) time.

        Args:
            task_ids: List of task IDs to retrieve

        Returns:
            Dictionary mapping task IDs to Task objects.
            Missing IDs are not included in the result.
        """
        return {
            task_id: task
            for task_id in task_ids
            if (task := self._task_index.get(task_id)) is not None
        }

    def get_position(self, task_id: int) -> int | None:
        """Get the position of a task in the task list.

        Args:
            task_id: The ID of the task

        Returns:
            The position (index) of the task, or None if not found
        """
        return self._task_position.get(task_id)

    def add_task(self, task: Task, position: int) -> None:
        """Add a task to the indexes.

        Args:
            task: The task to add
            position: The position of the task in the task list

        Raises:
            ValueError: If task doesn't have an ID
        """
        if task.id is None:
            msg = "Cannot index task without ID"
            raise ValueError(msg)
        self._task_index[task.id] = task
        self._task_position[task.id] = position

    def update_task(self, task: Task) -> None:
        """Update a task in the index.

        Only updates the task_index (not position).
        Use rebuild_position_index() if positions have changed.

        Args:
            task: The task to update

        Raises:
            ValueError: If task doesn't have an ID or doesn't exist in index
        """
        if task.id is None:
            msg = "Cannot update task without ID"
            raise ValueError(msg)
        if task.id not in self._task_index:
            msg = f"Task with ID {task.id} not found in index"
            raise ValueError(msg)
        self._task_index[task.id] = task

    def remove_task(self, task_id: int) -> None:
        """Remove a task from the indexes.

        Note: This only removes from indexes. Caller must rebuild position index
        if task list positions have changed.

        Args:
            task_id: The ID of the task to remove
        """
        self._task_index.pop(task_id, None)
        self._task_position.pop(task_id, None)

    def has_task(self, task_id: int) -> bool:
        """Check if a task exists in the index.

        Args:
            task_id: The ID of the task to check

        Returns:
            True if task exists, False otherwise
        """
        return task_id in self._task_index

    def rebuild_position_index(self, tasks: list[Task]) -> None:
        """Rebuild only the position index from task list.

        Useful after operations that change task positions (like deletion).

        Args:
            tasks: List of tasks with updated positions
        """
        self._task_position = {task.id: i for i, task in enumerate(tasks) if task.id is not None}
