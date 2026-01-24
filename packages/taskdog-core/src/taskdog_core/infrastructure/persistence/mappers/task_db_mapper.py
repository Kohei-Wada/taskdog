"""Database mapper for Task entity to SQLAlchemy ORM model.

This mapper handles conversion between Task domain entities and TaskModel
ORM instances, including JSON serialization for complex fields.

Phase 6 (Issue 228): Tags are stored exclusively in normalized tables (tags/task_tags).
The mapper reads/writes tags via the TaskModel.tag_models relationship.
"""

import json
from typing import Any

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.models.task_model import TaskModel
from taskdog_core.shared.utils.datetime_parser import format_date_dict, parse_date_dict

from .task_mapper_interface import TaskMapperInterface


class TaskDbMapper(TaskMapperInterface):
    """Mapper for converting Task entities to/from SQLAlchemy TaskModel.

    This mapper:
    - Converts Task entities to TaskModel ORM instances
    - Converts TaskModel ORM instances back to Task entities
    - Handles JSON serialization for complex fields (daily_allocations, tags, etc.)
    - Maintains data integrity during conversions
    """

    # Fields that can be mapped directly without transformation
    _DIRECT_FIELDS: tuple[str, ...] = (
        "id",
        "name",
        "priority",
        "created_at",
        "updated_at",
        "planned_start",
        "planned_end",
        "deadline",
        "actual_start",
        "actual_end",
        "actual_duration",
        "estimated_duration",
        "is_fixed",
        "is_archived",
    )

    def _get_serialized_fields(self, task: Task) -> dict[str, Any]:
        """Extract and serialize all fields from a Task entity.

        This method centralizes field extraction logic to avoid duplication
        across to_dict, to_model, and update_model methods.

        Args:
            task: The Task entity to serialize

        Returns:
            Dictionary with all fields ready for persistence
        """
        result: dict[str, Any] = {
            field: getattr(task, field) for field in self._DIRECT_FIELDS
        }
        # Fields requiring transformation
        result["status"] = task.status.value
        result["daily_allocations"] = json.dumps(
            format_date_dict(task.daily_allocations)
        )
        result["depends_on"] = json.dumps(task.depends_on)
        return result

    def to_dict(self, task: Task) -> dict[str, Any]:
        """Convert a Task entity to a dictionary (for ORM compatibility).

        This method is used when creating TaskModel instances via constructor.
        It prepares Task data in a format suitable for SQLAlchemy.

        Args:
            task: The Task entity to convert

        Returns:
            Dictionary with all fields ready for TaskModel creation
        """
        return self._get_serialized_fields(task)

    def to_model(self, task: Task) -> TaskModel:
        """Convert a Task entity to a TaskModel ORM instance.

        Args:
            task: The Task entity to convert

        Returns:
            TaskModel instance ready for database persistence
        """
        return TaskModel(**self._get_serialized_fields(task))

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
        # Note: priority can be None (nullable column)
        assert model.status is not None, "TaskModel.status must not be None"
        assert model.created_at is not None, "TaskModel.created_at must not be None"
        assert model.updated_at is not None, "TaskModel.updated_at must not be None"
        assert model.is_fixed is not None, "TaskModel.is_fixed must not be None"
        assert model.is_archived is not None, "TaskModel.is_archived must not be None"
        assert model.daily_allocations is not None, (
            "TaskModel.daily_allocations must not be None"
        )
        assert model.depends_on is not None, "TaskModel.depends_on must not be None"

        # Parse JSON fields
        daily_allocations = parse_date_dict(
            json.loads(model.daily_allocations) if model.daily_allocations else {}
        )
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
            actual_duration=model.actual_duration,
            estimated_duration=model.estimated_duration,
            is_fixed=model.is_fixed,
            daily_allocations=daily_allocations,
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
        for field, value in self._get_serialized_fields(task).items():
            if field != "id":  # id should not be updated
                setattr(model, field, value)
