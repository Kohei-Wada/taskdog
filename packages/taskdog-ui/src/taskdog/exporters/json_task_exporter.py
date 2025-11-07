"""JSON task exporter."""

import json

from taskdog.exporters.task_exporter import TaskExporter
from taskdog_core.application.dto.task_dto import TaskRowDto


class JsonTaskExporter(TaskExporter):
    """Exports tasks to JSON format."""

    def export(self, tasks: list[TaskRowDto]) -> str:
        """Export tasks to JSON string.

        Args:
            tasks: List of task DTOs to export

        Returns:
            JSON string representation of tasks
        """
        tasks_data = [self._filter_fields(task.to_dict()) for task in tasks]
        return json.dumps(tasks_data, indent=4, ensure_ascii=False)
