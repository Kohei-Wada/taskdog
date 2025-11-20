"""Database mapper for Task entity to SQLAlchemy ORM model.

This mapper handles conversion between Task domain entities and TaskModel
ORM instances, including JSON serialization for complex fields.

Phase 6 (Issue 228): Tags are stored exclusively in normalized tables (tags/task_tags).
The mapper reads/writes tags via the TaskModel.tag_models relationship.
"""

import json
from datetime import date
from typing import Any

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.models.task_model import TaskModel

from .task_mapper_interface import TaskMapperInterface


class TaskDbMapper(TaskMapperInterface):
    """Mapper for converting Task entities to/from SQLAlchemy TaskModel.

    This mapper:
    - Converts Task entities to TaskModel ORM instances
    - Converts TaskModel ORM instances back to Task entities
    - Handles JSON serialization for complex fields (daily_allocations, tags, etc.)
    - Maintains data integrity during conversions
    """

    def to_dict(self, task: Task) -> dict[str, Any]:
        """Convert a Task entity to a dictionary (for ORM compatibility).

        This method is used when creating TaskModel instances via constructor.
        It prepares Task data in a format suitable for SQLAlchemy.

        Args:
            task: The Task entity to convert

        Returns:
            Dictionary with all fields ready for TaskModel creation
        """
        return {
            "id": task.id,
            "name": task.name,
            "priority": task.priority,
            "status": task.status.value,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "planned_start": task.planned_start,
            "planned_end": task.planned_end,
            "deadline": task.deadline,
            "actual_start": task.actual_start,
            "actual_end": task.actual_end,
            "estimated_duration": task.estimated_duration,
            "is_fixed": task.is_fixed,
            "daily_allocations": self._serialize_date_dict(task.daily_allocations),
            "actual_daily_hours": self._serialize_date_dict(task.actual_daily_hours),
            "depends_on": json.dumps(task.depends_on),
            "is_archived": task.is_archived,
        }

    def from_dict(self, data: dict[str, Any]) -> Task:
        """Convert a dictionary (from ORM) to a Task entity.

        Args:
            data: Dictionary containing task data from TaskModel

        Returns:
            Task entity reconstructed from the data

        Raises:
            TaskValidationError: If the data violates Task entity invariants
        """
        # Parse complex JSON fields
        daily_allocations = self._deserialize_date_dict(
            data.get("daily_allocations", "{}")
        )
        actual_daily_hours = self._deserialize_date_dict(
            data.get("actual_daily_hours", "{}")
        )
        depends_on = json.loads(data.get("depends_on", "[]"))

        # Convert status string to Enum
        status = (
            TaskStatus(data["status"])
            if isinstance(data["status"], str)
            else data["status"]
        )

        return Task(
            id=data["id"],
            name=data["name"],
            priority=data["priority"],
            status=status,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            planned_start=data.get("planned_start"),
            planned_end=data.get("planned_end"),
            deadline=data.get("deadline"),
            actual_start=data.get("actual_start"),
            actual_end=data.get("actual_end"),
            estimated_duration=data.get("estimated_duration"),
            is_fixed=data.get("is_fixed", False),
            daily_allocations=daily_allocations,
            actual_daily_hours=actual_daily_hours,
            depends_on=depends_on,
            tags=[],  # Tags populated via tag_models relationship, not dict
            is_archived=data.get("is_archived", False),
        )

    def to_model(self, task: Task) -> TaskModel:
        """Convert a Task entity to a TaskModel ORM instance.

        Args:
            task: The Task entity to convert

        Returns:
            TaskModel instance ready for database persistence
        """
        return TaskModel(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status.value,
            created_at=task.created_at,
            updated_at=task.updated_at,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            estimated_duration=task.estimated_duration,
            is_fixed=task.is_fixed,
            daily_allocations=self._serialize_date_dict(task.daily_allocations),
            actual_daily_hours=self._serialize_date_dict(task.actual_daily_hours),
            depends_on=json.dumps(task.depends_on),
            is_archived=task.is_archived,
        )

    def from_model(self, model: TaskModel) -> Task:
        """Convert a TaskModel ORM instance to a Task entity.

        Args:
            model: The TaskModel instance from database

        Returns:
            Task entity reconstructed from the model

        Raises:
            TaskValidationError: If the model data violates Task entity invariants
        """
        # Validate required fields (database enforces NOT NULL constraints)
        assert model.name is not None, "TaskModel.name must not be None"
        assert model.priority is not None, "TaskModel.priority must not be None"
        assert model.status is not None, "TaskModel.status must not be None"
        assert model.created_at is not None, "TaskModel.created_at must not be None"
        assert model.updated_at is not None, "TaskModel.updated_at must not be None"
        assert model.is_fixed is not None, "TaskModel.is_fixed must not be None"
        assert model.is_archived is not None, "TaskModel.is_archived must not be None"
        assert model.daily_allocations is not None, (
            "TaskModel.daily_allocations must not be None"
        )
        assert model.actual_daily_hours is not None, (
            "TaskModel.actual_daily_hours must not be None"
        )
        assert model.depends_on is not None, "TaskModel.depends_on must not be None"

        # Parse JSON fields
        daily_allocations = self._deserialize_date_dict(model.daily_allocations)
        actual_daily_hours = self._deserialize_date_dict(model.actual_daily_hours)
        depends_on = json.loads(model.depends_on)

        # Phase 6: Get tags from normalized relationship only
        tags: list[str] = (
            [tag.name for tag in model.tag_models] if model.tag_models else []
        )

        return Task(
            id=model.id,
            name=model.name,
            priority=model.priority,
            status=TaskStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            planned_start=model.planned_start,
            planned_end=model.planned_end,
            deadline=model.deadline,
            actual_start=model.actual_start,
            actual_end=model.actual_end,
            estimated_duration=model.estimated_duration,
            is_fixed=model.is_fixed,
            daily_allocations=daily_allocations,
            actual_daily_hours=actual_daily_hours,
            depends_on=depends_on,
            tags=tags,
            is_archived=model.is_archived,
        )

    def update_model(self, model: TaskModel, task: Task) -> None:
        """Update an existing TaskModel instance with Task entity data.

        This method is useful for update operations where you want to modify
        an existing ORM instance rather than creating a new one.

        Args:
            model: The TaskModel instance to update
            task: The Task entity with new data
        """
        model.name = task.name
        model.priority = task.priority
        model.status = task.status.value
        model.created_at = task.created_at
        model.updated_at = task.updated_at
        model.planned_start = task.planned_start
        model.planned_end = task.planned_end
        model.deadline = task.deadline
        model.actual_start = task.actual_start
        model.actual_end = task.actual_end
        model.estimated_duration = task.estimated_duration
        model.is_fixed = task.is_fixed
        model.daily_allocations = self._serialize_date_dict(task.daily_allocations)
        model.actual_daily_hours = self._serialize_date_dict(task.actual_daily_hours)
        model.depends_on = json.dumps(task.depends_on)
        model.is_archived = task.is_archived

    @staticmethod
    def _serialize_date_dict(date_dict: dict[date, float]) -> str:
        """Serialize date dictionary to JSON string.

        Args:
            date_dict: Dictionary with date keys and float values

        Returns:
            JSON string representation
        """
        if not date_dict:
            return "{}"
        # Convert date keys to ISO format strings
        str_dict = {k.isoformat(): v for k, v in date_dict.items()}
        return json.dumps(str_dict)

    @staticmethod
    def _deserialize_date_dict(json_str: str) -> dict[date, float]:
        """Deserialize JSON string to date dictionary.

        Args:
            json_str: JSON string with date keys

        Returns:
            Dictionary with date object keys and float values
        """
        if not json_str or json_str == "{}":
            return {}

        str_dict = json.loads(json_str)
        result: dict[date, float] = {}

        for date_str, value in str_dict.items():
            try:
                date_obj = date.fromisoformat(date_str)
                result[date_obj] = value
            except (ValueError, AttributeError):
                # Skip invalid dates
                continue

        return result
