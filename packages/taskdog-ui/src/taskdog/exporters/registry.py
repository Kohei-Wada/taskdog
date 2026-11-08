"""Export formats shared by the CLI and TUI export commands."""

from taskdog.exporters.csv_task_exporter import CsvTaskExporter
from taskdog.exporters.json_task_exporter import JsonTaskExporter
from taskdog.exporters.markdown_table_exporter import MarkdownTableExporter
from taskdog.exporters.task_exporter import TaskExporter

EXPORTER_CLASSES: dict[str, type[TaskExporter]] = {
    "json": JsonTaskExporter,
    "csv": CsvTaskExporter,
    "markdown": MarkdownTableExporter,
}
"""Exporter class for each export format."""

EXPORT_FILE_EXTENSIONS: dict[str, str] = {
    "json": "json",
    "csv": "csv",
    "markdown": "md",
}
"""File extension for each export format."""


def create_exporter(
    export_format: str, field_list: list[str] | None = None
) -> TaskExporter:
    """Create the exporter for ``export_format``.

    Args:
        export_format: One of the keys of :data:`EXPORTER_CLASSES`
        field_list: Fields to export (``None`` uses the default fields)

    Returns:
        Exporter instance for the format

    Raises:
        ValueError: If the format is not supported
    """
    exporter_class = EXPORTER_CLASSES.get(export_format)
    if exporter_class is None:
        raise ValueError(f"Unsupported format: {export_format}")
    return exporter_class(field_list=field_list)
