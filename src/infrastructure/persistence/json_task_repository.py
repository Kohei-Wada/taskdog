from datetime import datetime
from typing import Any, cast

from domain.entities.task import Task
from domain.repositories.task_repository import TaskRepository
from infrastructure.persistence.json_task_storage import JsonTaskStorage
from infrastructure.persistence.task_index_manager import TaskIndexManager


class JsonTaskRepository(TaskRepository):
    """JSON file-based implementation of TaskRepository with index optimization.

    This repository uses composition to separate concerns:
    - JsonTaskStorage: Handles JSON I/O with atomic writes and backup
    - TaskIndexManager: Manages in-memory indexes for O(1) lookups
    """

    def __init__(self, filename: str):
        """Initialize the repository with a JSON file.

        Args:
            filename: Path to the JSON file for task storage
        """
        self.filename = filename
        self._storage = JsonTaskStorage()
        self.tasks = self._storage.load(filename)
        self._index_manager = TaskIndexManager(self.tasks)

    def get_all(self) -> list[Task]:
        """Retrieve all tasks.

        Returns:
            List of all tasks
        """
        return self.tasks

    def get_by_id(self, task_id: int) -> Task | None:
        """Retrieve a task by its ID in O(1) time.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        return self._index_manager.get_by_id(task_id)

    def get_by_ids(self, task_ids: list[int]) -> dict[int, Task]:
        """Retrieve multiple tasks by their IDs in O(n) time.

        Leverages the existing task index for O(1) lookup per task.

        Args:
            task_ids: List of task IDs to retrieve

        Returns:
            Dictionary mapping task IDs to Task objects.
            Missing IDs are not included in the result.
        """
        return self._index_manager.get_by_ids(task_ids)

    def _update_task_in_memory(self, task: Task) -> None:
        """Update a single task in memory (indexes and list).

        Args:
            task: The task to update

        Raises:
            ValueError: If task doesn't have an ID
        """
        # Task must have an ID (assigned by create() or from_dict())
        if task.id is None:
            msg = "Cannot save task without ID. Use create() to generate ID."
            raise ValueError(msg)

        # Check if task already exists
        if not self._index_manager.has_task(task.id):
            # New task - add to list and index
            position = len(self.tasks)
            self.tasks.append(task)
            self._index_manager.add_task(task, position)
        else:
            # Task exists - update the existing task in place
            # Automatically update the updated_at timestamp
            task.updated_at = datetime.now()

            # Use position index for O(1) access
            # Task is in index, so position must exist (cast for type checker)
            task_position = cast(int, self._index_manager.get_position(task.id))
            self.tasks[task_position] = task

            # Update task index to point to new object
            self._index_manager.update_task(task)

    def save(self, task: Task) -> None:
        """Save a task (create new or update existing).

        Args:
            task: The task to save
        """
        self._update_task_in_memory(task)
        self._storage.save(self.filename, self.tasks)

    def save_all(self, tasks: list[Task]) -> None:
        """Save multiple tasks atomically.

        Args:
            tasks: List of tasks to save

        Raises:
            ValueError: If any task doesn't have an ID
        """
        # Early return for empty list
        if not tasks:
            return

        # Update in-memory state for all tasks
        for task in tasks:
            self._update_task_in_memory(task)

        # Single file write at the end (atomic operation)
        self._storage.save(self.filename, self.tasks)

    def delete(self, task_id: int) -> None:
        """Delete a task by its ID.

        Args:
            task_id: The ID of the task to delete
        """
        # Use position index for O(1) lookup
        position = self._index_manager.get_position(task_id)
        if position is not None:
            self.tasks.pop(position)
            # Remove from index and rebuild position index as positions have shifted
            self._index_manager.remove_task(task_id)
            self._index_manager.rebuild_position_index(self.tasks)
            self._storage.save(self.filename, self.tasks)

    def create(self, name: str, priority: int, **kwargs: Any) -> Task:
        """Create a new task with auto-generated ID and save it.

        Args:
            name: Task name
            priority: Task priority
            **kwargs: Additional task fields (deadline, estimated_duration, etc.)

        Returns:
            Created task with ID assigned
        """
        task_id = self.generate_next_id()
        task = Task(id=task_id, name=name, priority=priority, **kwargs)
        self.save(task)
        return task

    def generate_next_id(self) -> int:
        """Generate the next available task ID.

        Returns:
            The next available ID (1 if no tasks exist, otherwise max(id) + 1)
        """
        if not self.tasks:
            return 1
        # Filter out tasks without IDs (should not happen in normal operation)
        task_ids = [task.id for task in self.tasks if task.id is not None]
        return max(task_ids) + 1 if task_ids else 1

    def reload(self) -> None:
        """Reload tasks from JSON file.

        This method refreshes the in-memory cache from the JSON file,
        allowing detection of changes made by external processes.
        """
        self.tasks = self._storage.load(self.filename)
        self._index_manager.build_indexes(self.tasks)
