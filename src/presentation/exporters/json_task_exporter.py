"""JSON task exporter."""

import json

from domain.entities.task import Task
from presentation.exporters.task_exporter import TaskExporter


class JsonTaskExporter(TaskExporter):
    """Exports tasks to JSON format."""

    def export(self, tasks: list[Task]) -> str:
        """Export tasks to JSON string.

        Args:
            tasks: List of tasks to export

        Returns:
            JSON string representation of tasks
        """
        tasks_data = [self._filter_fields(task.to_dict()) for task in tasks]
        return json.dumps(tasks_data, indent=4, ensure_ascii=False)
