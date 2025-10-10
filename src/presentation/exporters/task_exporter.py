"""Abstract base class for task exporters."""

from abc import ABC, abstractmethod

from domain.entities.task import Task


class TaskExporter(ABC):
    """Abstract base class for exporting tasks to different formats.

    Subclasses must implement the export method to provide format-specific
    export functionality.
    """

    def __init__(self, field_list: list[str] | None = None):
        """Initialize the exporter.

        Args:
            field_list: List of field names to export. If None, export all fields.
        """
        self.field_list = field_list

    @abstractmethod
    def export(self, tasks: list[Task]) -> str:
        """Export tasks to a string in the specific format.

        Args:
            tasks: List of tasks to export

        Returns:
            String representation of tasks in the target format
        """
        pass

    def _filter_fields(self, task_dict: dict) -> dict:
        """Filter task dictionary to include only specified fields.

        Args:
            task_dict: Full task dictionary

        Returns:
            Filtered dictionary with only specified fields (or all if field_list is None)
        """
        if self.field_list is None:
            return task_dict

        return {field: task_dict.get(field) for field in self.field_list}
