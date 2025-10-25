"""CSV task exporter."""

import csv
import io
import json

from domain.entities.task import Task
from presentation.exporters.task_exporter import TaskExporter

# Default fields for CSV export when no specific fields are requested
DEFAULT_CSV_FIELDS = [
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


class CsvTaskExporter(TaskExporter):
    """Exports tasks to CSV format."""

    def export(self, tasks: list[Task]) -> str:
        """Export tasks to CSV string.

        Args:
            tasks: List of tasks to export

        Returns:
            CSV string representation of tasks
        """
        # Determine fields to export
        fields = self.field_list or DEFAULT_CSV_FIELDS

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()

        for task in tasks:
            row = self._filter_fields(task.to_dict())
            # Convert complex fields (dict) to JSON string for CSV compatibility
            if row.get("daily_allocations"):
                row["daily_allocations"] = json.dumps(row["daily_allocations"])
            # Ensure all fields exist (fill with empty string if missing)
            writer.writerow({k: row.get(k, "") for k in fields})

        return output.getvalue()
