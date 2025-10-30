"""Markdown table task exporter."""

from datetime import date, datetime
from typing import Any

from domain.entities.task import Task
from presentation.exporters.task_exporter import TaskExporter

# Default fields for Markdown table export when no specific fields are requested
DEFAULT_MARKDOWN_FIELDS = [
    "id",
    "name",
    "priority",
    "status",
    "deadline",
    "planned_start",
    "planned_end",
    "estimated_duration",
]


class MarkdownTableExporter(TaskExporter):
    """Exports tasks to Markdown table format."""

    def export(self, tasks: list[Task]) -> str:
        """Export tasks to Markdown table string.

        Args:
            tasks: List of tasks to export

        Returns:
            Markdown table string representation of tasks
        """
        # Determine fields to export
        fields = self.field_list or DEFAULT_MARKDOWN_FIELDS

        # Create markdown table
        lines = []

        # Header row
        header = "|" + "|".join(self._format_field_name(field) for field in fields) + "|"
        lines.append(header)

        # Separator row
        separator = "|" + "|".join("--" for _ in fields) + "|"
        lines.append(separator)

        # Data rows
        for task in tasks:
            task_dict = self._filter_fields(task.to_dict())
            row_values = [self._format_value(task_dict.get(field)) for field in fields]
            row = "|" + "|".join(row_values) + "|"
            lines.append(row)

        return "\n".join(lines)

    def _format_field_name(self, field: str) -> str:
        """Format field name for display in table header.

        Args:
            field: Field name

        Returns:
            Formatted field name
        """
        # Convert snake_case to Title Case
        return field.replace("_", " ").title()

    def _format_value(self, value: Any) -> str:
        """Format value for display in markdown table cell.

        Args:
            value: Value to format

        Returns:
            Formatted string representation
        """
        if value is None:
            return "-"

        # Handle datetime objects
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")

        # Handle date objects
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")

        # Handle boolean (check before dict/list since bool is a subclass of int)
        if isinstance(value, bool):
            return "✓" if value else "✗"

        # Handle dictionaries (e.g., daily_allocations)
        if isinstance(value, dict):
            return self._format_dict(value)

        # Handle lists
        if isinstance(value, list):
            return self._format_list(value)

        # Handle ISO format datetime strings from to_dict()
        if isinstance(value, str):
            return self._format_string(value)

        # Default: convert to string
        return str(value)

    def _format_dict(self, value: dict[str, Any]) -> str:
        """Format dictionary value for display.

        Args:
            value: Dictionary to format

        Returns:
            Formatted string
        """
        if not value:
            return "-"
        # Format as compact representation
        items = [f"{k}: {v}" for k, v in value.items()]
        return ", ".join(items[:3])  # Limit to first 3 items to avoid overly long cells

    def _format_list(self, value: list[Any]) -> str:
        """Format list value for display.

        Args:
            value: List to format

        Returns:
            Formatted string
        """
        if not value:
            return "-"
        return ", ".join(str(item) for item in value)

    def _format_string(self, value: str) -> str:
        """Format string value, converting ISO datetime format if applicable.

        Args:
            value: String to format

        Returns:
            Formatted string
        """
        if "T" in value:
            # Convert ISO 8601 datetime format (2025-10-31T09:00:00) to space-separated
            # Only replace T if it looks like an ISO datetime (contains digits before and after T)
            parts = value.split("T")
            if len(parts) == 2 and "-" in parts[0] and ":" in parts[1]:
                return value.replace("T", " ")
        return value
