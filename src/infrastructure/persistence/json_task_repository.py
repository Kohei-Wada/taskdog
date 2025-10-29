import contextlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository
from shared.constants.file_management import BACKUP_FILE_SUFFIX


class JsonTaskRepository(TaskRepository):
    """JSON file-based implementation of TaskRepository with index optimization."""

    def __init__(self, filename: str):
        """Initialize the repository with a JSON file.

        Args:
            filename: Path to the JSON file for task storage
        """
        self.filename = filename
        self.tasks = self._load_tasks()
        self._task_index: dict[int, Task] = self._build_index()
        self._task_position: dict[int, int] = self._build_position_index()

    def _build_index(self) -> dict[int, Task]:
        """Build task ID to task object index.

        Returns:
            Dictionary mapping task IDs to task objects
        """
        return {task.id: task for task in self.tasks if task.id is not None}

    def _build_position_index(self) -> dict[int, int]:
        """Build task ID to list position index for O(1) access.

        Returns:
            Dictionary mapping task IDs to their position in self.tasks
        """
        return {task.id: i for i, task in enumerate(self.tasks) if task.id is not None}

    def _rebuild_index(self) -> None:
        """Rebuild the task index after modifications."""
        self._task_index = self._build_index()
        self._task_position = self._build_position_index()

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
        return self._task_index.get(task_id)

    def get_by_ids(self, task_ids: list[int]) -> dict[int, Task]:
        """Retrieve multiple tasks by their IDs in O(n) time.

        Leverages the existing _task_index for O(1) lookup per task.

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

    def save(self, task: Task) -> None:
        """Save a task (create new or update existing).

        Args:
            task: The task to save
        """
        # Task must have an ID (assigned by create() or from_dict())
        if task.id is None:
            msg = "Cannot save task without ID. Use create() to generate ID."
            raise ValueError(msg)

        # Check if task already exists
        existing = self._task_index.get(task.id)
        if not existing:
            # New task - add to list and both indexes
            position = len(self.tasks)
            self.tasks.append(task)
            self._task_index[task.id] = task
            self._task_position[task.id] = position
        else:
            # Task exists - update the existing task in place
            # Automatically update the updated_at timestamp
            task.updated_at = datetime.now()

            # Use position index for O(1) access instead of O(n) search
            position = self._task_position[task.id]
            self.tasks[position] = task

            # Update task index to point to new object
            self._task_index[task.id] = task

        # Save to file
        self._save_to_file()

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
            # Task must have an ID (assigned by create() or from_dict())
            if task.id is None:
                msg = "Cannot save task without ID. Use create() to generate ID."
                raise ValueError(msg)

            # Check if task already exists
            existing = self._task_index.get(task.id)
            if not existing:
                # New task - add to list and both indexes
                position = len(self.tasks)
                self.tasks.append(task)
                self._task_index[task.id] = task
                self._task_position[task.id] = position
            else:
                # Task exists - update the existing task in place
                # Automatically update the updated_at timestamp
                task.updated_at = datetime.now()

                # Use position index for O(1) access instead of O(n) search
                position = self._task_position[task.id]
                self.tasks[position] = task

                # Update task index to point to new object
                self._task_index[task.id] = task

        # Single file write at the end (atomic operation)
        self._save_to_file()

    def delete(self, task_id: int) -> None:
        """Delete a task by its ID.

        Args:
            task_id: The ID of the task to delete
        """
        # Use position index for O(1) lookup instead of O(n) list comprehension
        position = self._task_position.get(task_id)
        if position is not None:
            self.tasks.pop(position)
            # Rebuild indexes as positions have shifted
            self._rebuild_index()
            self._save_to_file()

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

    def _load_tasks(self) -> list[Task]:
        """Load tasks from JSON file with fallback to backup.

        Returns:
            List of tasks loaded from file, or empty list if file doesn't exist

        Raises:
            IOError: If both main file and backup are corrupted
            CorruptedDataError: If tasks contain invalid data that violates entity invariants
        """
        # Try loading from main file
        try:
            with open(self.filename, encoding="utf-8") as f:
                content = f.read().strip()
                # Empty file is valid, return empty list
                if not content:
                    return []
                tasks_data = json.loads(content)
                return self._parse_tasks(tasks_data)
        except FileNotFoundError:
            # File doesn't exist yet, return empty list
            return []
        except json.JSONDecodeError as e:
            # Corrupted file, try backup
            return self._load_from_backup(e)

    def _load_from_backup(self, original_error: json.JSONDecodeError) -> list[Task]:
        """Load tasks from backup file and restore main file.

        Args:
            original_error: The JSONDecodeError from the main file

        Returns:
            List of tasks loaded from backup

        Raises:
            OSError: If both main file and backup are corrupted
        """
        backup_path = Path(self.filename).with_suffix(BACKUP_FILE_SUFFIX)
        if backup_path.exists():
            try:
                with open(backup_path, encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        return []
                    tasks_data = json.loads(content)
                    # Restore from backup
                    shutil.copy2(backup_path, self.filename)
                    return self._parse_tasks(tasks_data)
            except (OSError, json.JSONDecodeError):
                pass

        # Both main and backup failed
        raise OSError(
            f"Failed to load tasks: corrupted data file ({original_error})"
        ) from original_error

    def _parse_tasks(self, tasks_data: list[dict[str, Any]]) -> list[Task]:
        """Parse task data and validate entity invariants.

        Args:
            tasks_data: List of task dictionaries from JSON

        Returns:
            List of valid Task instances

        Raises:
            CorruptedDataError: If any task contains invalid data
        """
        from domain.exceptions.task_exceptions import CorruptedDataError, TaskValidationError

        tasks = []
        corrupted_tasks = []

        for data in tasks_data:
            try:
                task = Task.from_dict(data)
                tasks.append(task)
            except TaskValidationError as e:
                # Collect corrupted task info
                corrupted_tasks.append({"data": data, "error": str(e)})

        # If any tasks are corrupted, raise error with details
        if corrupted_tasks:
            raise CorruptedDataError(corrupted_tasks)

        return tasks

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
        self.tasks = self._load_tasks()
        self._rebuild_index()

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
                backup_path = file_path.with_suffix(BACKUP_FILE_SUFFIX)
                shutil.copy2(self.filename, backup_path)

            # Atomic rename (on Unix) or best-effort on Windows
            shutil.move(temp_path, self.filename)

        except Exception as e:
            # Clean up temp file on error
            with contextlib.suppress(OSError):
                os.unlink(temp_path)
            raise OSError(f"Failed to save tasks to {self.filename}: {e}") from e
