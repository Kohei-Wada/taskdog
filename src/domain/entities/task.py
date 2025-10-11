import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

from domain.constants import DATETIME_FORMAT


class TaskStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Task:
    def __init__(
        self,
        name,
        priority,
        id=None,
        status=None,
        timestamp=None,
        parent_id=None,
        planned_start=None,
        planned_end=None,
        deadline=None,
        actual_start=None,
        actual_end=None,
        estimated_duration=None,
    ):
        self.id = id  # Will be set by TaskManager
        self.name = name
        self.priority = priority
        self.status = status or TaskStatus.PENDING
        self.timestamp = timestamp or time.time()
        self.parent_id = parent_id

        # Time management fields
        self.planned_start = planned_start
        self.planned_end = planned_end
        self.deadline = deadline
        self.actual_start = actual_start
        self.actual_end = actual_end
        self.estimated_duration = estimated_duration  # in hours

    @property
    def created_at_str(self):
        """Return human-readable creation timestamp"""
        return datetime.fromtimestamp(self.timestamp).strftime(DATETIME_FORMAT)

    @property
    def actual_duration_hours(self):
        """Calculate actual duration in hours from actual_start and actual_end"""
        if not self.actual_start or not self.actual_end:
            return None

        start = datetime.strptime(self.actual_start, DATETIME_FORMAT)
        end = datetime.strptime(self.actual_end, DATETIME_FORMAT)
        duration = (end - start).total_seconds() / 3600
        return round(duration, 1)

    @property
    def notes_path(self) -> Path:
        """Return path to task's markdown notes file.

        Returns:
            Path to notes file at $XDG_DATA_HOME/taskdog/notes/{id}.md
        """
        data_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        notes_dir = Path(data_dir) / "taskdog" / "notes"
        return notes_dir / f"{self.id}.md"

    def to_dict(self) -> dict:
        """Serialize task to dictionary for persistence.

        Returns:
            Dictionary containing all task fields
        """
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "parent_id": self.parent_id,
            "planned_start": self.planned_start,
            "planned_end": self.planned_end,
            "deadline": self.deadline,
            "actual_start": self.actual_start,
            "actual_end": self.actual_end,
            "estimated_duration": self.estimated_duration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Deserialize task from dictionary.

        Args:
            data: Dictionary containing task fields

        Returns:
            Task instance
        """
        # Convert status string to Enum if present
        task_data = data.copy()
        if "status" in task_data and isinstance(task_data["status"], str):
            task_data["status"] = TaskStatus(task_data["status"])
        return cls(**task_data)

    def __repr__(self):
        return f"Task({self.name}, {self.priority}, {self.status.value})"
