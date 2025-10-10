import json
import os
import tempfile
import shutil
from pathlib import Path
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
        self._children_index: Dict[int, List[Task]] = self._build_children_index()

    def _build_index(self) -> Dict[int, Task]:
        """Build task ID to task object index.

        Returns:
            Dictionary mapping task IDs to task objects
        """
        return {task.id: task for task in self.tasks}

    def _build_children_index(self) -> Dict[int, List[Task]]:
        """Build parent ID to children list index.

        Returns:
            Dictionary mapping parent task IDs to lists of child tasks
        """
        children_index: Dict[int, List[Task]] = {}
        for task in self.tasks:
            if task.parent_id is not None:
                if task.parent_id not in children_index:
                    children_index[task.parent_id] = []
                children_index[task.parent_id].append(task)
        return children_index

    def _rebuild_index(self) -> None:
        """Rebuild the task index after modifications."""
        self._task_index = self._build_index()
        self._children_index = self._build_children_index()

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
        """Retrieve all child tasks of a given task in O(1) time.

        Args:
            task_id: The ID of the parent task

        Returns:
            List of child tasks (empty list if no children)
        """
        return self._children_index.get(task_id, [])

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

            # Update children index if this task has a parent
            if task.parent_id is not None:
                if task.parent_id not in self._children_index:
                    self._children_index[task.parent_id] = []
                self._children_index[task.parent_id].append(task)
        else:
            # Task exists - update the existing task in place
            # Find the task in self.tasks list and replace it
            for i, t in enumerate(self.tasks):
                if t.id == task.id:
                    self.tasks[i] = task
                    break

            # Update index to point to new object
            self._task_index[task.id] = task

            # Check if parent_id changed
            if existing.parent_id != task.parent_id:
                # Parent changed - rebuild children index
                self._children_index = self._build_children_index()
            else:
                # Update children index if task has a parent
                if task.parent_id is not None:
                    # Rebuild children for this parent
                    if task.parent_id in self._children_index:
                        # Replace the child in the list
                        children = self._children_index[task.parent_id]
                        for i, child in enumerate(children):
                            if child.id == task.id:
                                children[i] = task
                                break

        # Save to file
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
        """Load tasks from JSON file with fallback to backup.

        Returns:
            List of tasks loaded from file, or empty list if file doesn't exist

        Raises:
            IOError: If both main file and backup are corrupted
        """
        # Try loading from main file
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Empty file is valid, return empty list
                if not content:
                    return []
                tasks_data = json.loads(content)
                return [Task.from_dict(data) for data in tasks_data]
        except FileNotFoundError:
            # File doesn't exist yet, return empty list
            return []
        except json.JSONDecodeError as e:
            # Corrupted file, try backup
            backup_path = Path(self.filename).with_suffix(".json.bak")
            if backup_path.exists():
                try:
                    with open(backup_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if not content:
                            return []
                        tasks_data = json.loads(content)
                        # Restore from backup
                        shutil.copy2(backup_path, self.filename)
                        return [Task.from_dict(data) for data in tasks_data]
                except (json.JSONDecodeError, IOError):
                    pass

            # Both main and backup failed
            raise IOError(f"Failed to load tasks: corrupted data file ({e})") from e

    def generate_next_id(self) -> int:
        """Generate the next available task ID.

        Returns:
            The next available ID (1 if no tasks exist, otherwise max(id) + 1)
        """
        if not self.tasks:
            return 1
        return max(task.id for task in self.tasks) + 1

    def _save_to_file(self) -> None:
        """Save all tasks to JSON file with atomic write and backup.

        Process:
        1. Write to temporary file
        2. Create backup of existing file
        3. Atomically rename temp file to target file

        This ensures data integrity even if the process is interrupted.
        """
        # Ensure directory exists
        file_path = Path(self.filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data
        tasks_data = [task.to_dict() for task in self.tasks]

        # Write to temporary file in the same directory (important for atomic rename)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent, prefix=f".{file_path.name}.", suffix=".tmp"
        )

        try:
            # Write to temp file
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, indent=4, ensure_ascii=False)

            # Create backup if original file exists
            if file_path.exists():
                backup_path = file_path.with_suffix(".json.bak")
                shutil.copy2(self.filename, backup_path)

            # Atomic rename (on Unix) or best-effort on Windows
            shutil.move(temp_path, self.filename)

        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise IOError(f"Failed to save tasks to {self.filename}: {e}") from e
