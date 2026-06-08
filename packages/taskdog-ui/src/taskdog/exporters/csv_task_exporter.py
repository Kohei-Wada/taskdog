"""CSV task exporter."""

import csv
import io

from taskdog.exporters.task_exporter import TaskExporter
from taskdog_core.application.dto.task_dto import TaskRowDto


class CsvTaskExporter(TaskExporter):
    """Exports tasks to CSV format."""

    def export(self, tasks: list[TaskRowDto]) -> str:
        """Export tasks to a CSV string."""
        output = io.StringIO()
        writer = csv.DictWriter(
            output, fieldnames=self.field_list, extrasaction="ignore"
        )
        writer.writeheader()

        for task in tasks:
            row = self._filter_fields(task.to_dict())
            writer.writerow({k: row.get(k, "") for k in self.field_list})

        return output.getvalue()
