import json
from typing import Dict, List, Optional
from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository


class JsonTaskRepository(TaskRepository):
    """JSON file-based implementation of TaskRepository with index optimization."""

    def __init__(self, filename: str):
        """Initialize the repository with a JSON file.

        Args:
            filename: Path to the JSON file for task storage
        """
        self.filename = filename
        self.tasks = self._load_tasks()
        self._task_index: Dict[int, Task] = self._build_index()

    def _build_index(self) -> Dict[int, Task]:
        """Build task ID to task object index.

        Returns:
            Dictionary mapping task IDs to task objects
        """
        return {task.id: task for task in self.tasks}

    def _rebuild_index(self) -> None:
        """Rebuild the task index after modifications."""
        self._task_index = self._build_index()

    def get_all(self) -> List[Task]:
        """Retrieve all tasks.

        Returns:
            List of all tasks
        """
        return self.tasks

    def get_by_id(self, task_id: int) -> Optional[Task]:
        """Retrieve a task by its ID in O(1) time.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        return self._task_index.get(task_id)

    def get_children(self, task_id: int) -> List[Task]:
        """Retrieve all child tasks of a given task.

        Args:
            task_id: The ID of the parent task

        Returns:
            List of child tasks
        """
        return [task for task in self.tasks if task.parent_id == task_id]

    def save(self, task: Task) -> None:
        """Save a task (create new or update existing).

        Args:
            task: The task to save
        """
        # Check if task already exists
        existing = self._task_index.get(task.id)
        if not existing:
            # New task - add to list and index
            self.tasks.append(task)
            self._task_index[task.id] = task

        # Save to file (existing task is already updated in-place)
        self._save_to_file()

    def delete(self, task_id: int) -> None:
        """Delete a task by its ID.

        Args:
            task_id: The ID of the task to delete
        """
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self._rebuild_index()
        self._save_to_file()

    def create(self, name: str, priority: int, **kwargs) -> Task:
        """Create a new task with auto-generated ID and save it.

        Args:
            name: Task name
            priority: Task priority
            **kwargs: Additional task fields (parent_id, deadline, etc.)

        Returns:
            Created task with ID assigned
        """
        task_id = self.generate_next_id()

        task = Task(id=task_id, name=name, priority=priority, **kwargs)

        self.save(task)
        return task

    def _load_tasks(self) -> List[Task]:
        """Load tasks from JSON file.

        Returns:
            List of tasks loaded from file, or empty list if file doesn't exist
        """
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)
                return [Task.from_dict(data) for data in tasks_data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def generate_next_id(self) -> int:
        """Generate the next available task ID.

        Returns:
            The next available ID (1 if no tasks exist, otherwise max(id) + 1)
        """
        if not self.tasks:
            return 1
        return max(task.id for task in self.tasks) + 1

    def _save_to_file(self) -> None:
        """Save all tasks to JSON file."""
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(
                [task.to_dict() for task in self.tasks], f, indent=4, ensure_ascii=False
            )
