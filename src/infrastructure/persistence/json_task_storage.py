"""JSON storage for tasks with atomic writes and backup recovery.

This module handles all JSON file I/O operations for task persistence,
including atomic writes and automatic recovery from backup files.
"""

import contextlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from domain.entities.task import Task
from shared.constants.file_management import BACKUP_FILE_SUFFIX


class JsonTaskStorage:
    """Handles JSON file storage operations with atomic writes and backup.

    Provides safe, atomic write operations and automatic recovery from backup
    when the main file is corrupted.
    """

    def load(self, filename: str) -> list[Task]:
        """Load tasks from JSON file with fallback to backup.

        Args:
            filename: Path to the JSON file

        Returns:
            List of tasks loaded from file, or empty list if file doesn't exist

        Raises:
            OSError: If both main file and backup are corrupted
            CorruptedDataError: If tasks contain invalid data that violates entity invariants
        """
        # Try loading from main file
        try:
            with open(filename, encoding="utf-8") as f:
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
            return self._load_from_backup(filename, e)

    def save(self, filename: str, tasks: list[Task]) -> None:
        """Save all tasks to JSON file with atomic write and backup.

        Process:
        1. Write to temporary file
        2. Create backup of existing file
        3. Atomically rename temp file to target file

        This ensures data integrity even if the process is interrupted.

        Args:
            filename: Path to the JSON file
            tasks: List of tasks to save

        Raises:
            OSError: If save operation fails
        """
        # Ensure directory exists
        file_path = Path(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data
        tasks_data = [task.to_dict() for task in tasks]

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
                shutil.copy2(filename, backup_path)

            # Atomic rename (on Unix) or best-effort on Windows
            shutil.move(temp_path, filename)

        except Exception as e:
            # Clean up temp file on error
            with contextlib.suppress(OSError):
                os.unlink(temp_path)
            raise OSError(f"Failed to save tasks to {filename}: {e}") from e

    def _load_from_backup(self, filename: str, original_error: json.JSONDecodeError) -> list[Task]:
        """Load tasks from backup file and restore main file.

        Args:
            filename: Path to the main JSON file
            original_error: The JSONDecodeError from the main file

        Returns:
            List of tasks loaded from backup

        Raises:
            OSError: If both main file and backup are corrupted
        """
        backup_path = Path(filename).with_suffix(BACKUP_FILE_SUFFIX)
        if backup_path.exists():
            try:
                with open(backup_path, encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        return []
                    tasks_data = json.loads(content)
                    # Restore from backup
                    shutil.copy2(backup_path, filename)
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
