"""JSON mapper for Task entity serialization.

This mapper handles conversion between Task entities and JSON-compatible
dictionaries, including datetime serialization and backward compatibility logic.
"""

from datetime import date, datetime
from typing import Any

from domain.entities.task import Task, TaskStatus

from .task_mapper_interface import TaskMapperInterface


class TaskJsonMapper(TaskMapperInterface):
    """Mapper for converting Task entities to/from JSON-compatible dictionaries.

    This mapper handles:
    - Datetime field serialization to ISO 8601 format
    - Dictionary key conversion for date-based fields
    - Enum conversion for TaskStatus
    - Backward compatibility with legacy data formats
    """

    def to_dict(self, task: Task) -> dict[str, Any]:
        """Convert a Task entity to a JSON-compatible dictionary.

        Datetime fields are serialized to ISO 8601 format strings.
        Date dictionary keys are converted to ISO format strings.

        Args:
            task: The Task entity to serialize

        Returns:
            Dictionary containing all task fields in JSON-compatible format
        """
        return {
            "id": task.id,
            "name": task.name,
            "priority": task.priority,
            "status": task.status.value,
            "created_at": self._serialize_datetime(task.created_at),
            "updated_at": self._serialize_datetime(task.updated_at),
            "planned_start": self._serialize_datetime(task.planned_start),
            "planned_end": self._serialize_datetime(task.planned_end),
            "deadline": self._serialize_datetime(task.deadline),
            "actual_start": self._serialize_datetime(task.actual_start),
            "actual_end": self._serialize_datetime(task.actual_end),
            "estimated_duration": task.estimated_duration,
            "daily_allocations": {k.isoformat(): v for k, v in task.daily_allocations.items()}
            if task.daily_allocations
            else {},
            "depends_on": task.depends_on,
            "is_fixed": task.is_fixed,
            "actual_daily_hours": {k.isoformat(): v for k, v in task.actual_daily_hours.items()}
            if task.actual_daily_hours
            else {},
            "tags": task.tags,
            "is_archived": task.is_archived,
        }

    def from_dict(self, data: dict[str, Any]) -> Task:
        """Convert a dictionary to a Task entity.

        Supports backward compatibility:
        - Legacy "is_deleted" field migrated to "is_archived"
        - Missing "is_archived" and "tags" fields initialized with defaults
        - ISO 8601 datetime format parsing

        Args:
            data: Dictionary containing task data from JSON storage

        Returns:
            Task entity reconstructed from the data

        Raises:
            TaskValidationError: If the data violates Task entity invariants
        """
        task_data = data.copy()

        # Backward compatibility: migrate is_deleted to is_archived
        if "is_deleted" in task_data:
            is_deleted = task_data.pop("is_deleted")
            if is_deleted:
                task_data["is_archived"] = True

        # Convert status string to Enum if present
        if "status" in task_data and isinstance(task_data["status"], str):
            task_data["status"] = TaskStatus(task_data["status"])

        # Convert datetime string fields to datetime objects
        datetime_fields = [
            "created_at",
            "updated_at",
            "planned_start",
            "planned_end",
            "deadline",
            "actual_start",
            "actual_end",
        ]
        for field_name in datetime_fields:
            if field_name in task_data and isinstance(task_data[field_name], str):
                task_data[field_name] = self._parse_datetime_string(task_data[field_name])

        # Convert daily_allocations from dict[str, float] to dict[date, float]
        if "daily_allocations" in task_data and isinstance(task_data["daily_allocations"], dict):
            task_data["daily_allocations"] = self._parse_date_dict(task_data["daily_allocations"])

        # Convert actual_daily_hours from dict[str, float] to dict[date, float]
        if "actual_daily_hours" in task_data and isinstance(task_data["actual_daily_hours"], dict):
            task_data["actual_daily_hours"] = self._parse_date_dict(task_data["actual_daily_hours"])

        # Backward compatibility: initialize is_archived as False if not present
        if "is_archived" not in task_data:
            task_data["is_archived"] = False

        # Backward compatibility: initialize tags as empty list if not present
        if "tags" not in task_data:
            task_data["tags"] = []

        return Task(**task_data)

    @staticmethod
    def _serialize_datetime(dt: datetime | str | None) -> str | None:
        """Serialize datetime to ISO 8601 string.

        Args:
            dt: Datetime object, string, or None

        Returns:
            ISO 8601 string if datetime object, original value otherwise
        """
        if isinstance(dt, datetime):
            return dt.isoformat()
        return dt

    @staticmethod
    def _parse_datetime_string(dt_str: str | None) -> datetime | None:
        """Parse datetime string in ISO 8601 format.

        Args:
            dt_str: Datetime string in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)

        Returns:
            datetime object or None if parsing fails
        """
        if not dt_str:
            return None

        try:
            return datetime.fromisoformat(dt_str)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _parse_date_dict(date_dict: dict[str, float]) -> dict[date, float]:
        """Parse dictionary with date string keys to date object keys.

        Args:
            date_dict: Dictionary with date strings as keys (YYYY-MM-DD format)

        Returns:
            Dictionary with date objects as keys
        """
        result: dict[date, float] = {}
        for date_str, value in date_dict.items():
            try:
                # Parse ISO format date string
                date_obj = date.fromisoformat(date_str)
                result[date_obj] = value
            except (ValueError, AttributeError):
                # Skip invalid date strings
                pass
        return result
