"""Abstract base class for task exporters."""

from abc import ABC, abstractmethod
from typing import Any

from taskdog_core.application.dto.task_dto import TaskRowDto

DEFAULT_EXPORT_FIELDS: list[str] = [
    "id",
    "name",
    "priority",
    "status",
    "deadline",
    "planned_start",
    "planned_end",
    "estimated_duration",
    "actual_start",
    "actual_end",
    "created_at",
]


class TaskExporter(ABC):
    """Abstract base class for exporting tasks to different formats.

    Subclasses must implement the export method to provide format-specific
    export functionality.
    """

    def __init__(self, field_list: list[str] | None = None):
        """Initialize the exporter.

        Args:
            field_list: Field names to export. ``None`` falls back to
                :data:`DEFAULT_EXPORT_FIELDS` so every format renders the same
                columns by default.
        """
        self.field_list = (
            list(field_list) if field_list is not None else list(DEFAULT_EXPORT_FIELDS)
        )

    @abstractmethod
    def export(self, tasks: list[TaskRowDto]) -> str:
        """Export tasks to a string in the specific format.

        Args:
            tasks: List of task DTOs to export

        Returns:
            String representation of tasks in the target format
        """

    def _filter_fields(self, task_dict: dict[str, Any]) -> dict[str, Any]:
        """Filter ``task_dict`` down to ``self.field_list`` (preserving order)."""
        return {field: task_dict.get(field) for field in self.field_list}
