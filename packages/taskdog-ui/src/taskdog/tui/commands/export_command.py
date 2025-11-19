"""Export command for TUI."""

from pathlib import Path
from typing import TYPE_CHECKING

from taskdog.exporters import (
    CsvTaskExporter,
    JsonTaskExporter,
    MarkdownTableExporter,
)
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.constants.ui_settings import EXPORT_FORMAT_CONFIG
from taskdog.tui.context import TUIContext
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


@command_registry.register("export")
class ExportCommand(TUICommandBase):
    """Command to export tasks to various formats.

    Exports all tasks to a file in the specified format (JSON, CSV, or Markdown).
    """

    def __init__(
        self,
        app: "TaskdogTUI",
        context: TUIContext,
        format_key: str = "",
    ) -> None:
        """Initialize the command.

        Args:
            app: The TaskdogTUI application instance
            context: TUI context with dependencies
            format_key: Export format (json, csv, markdown)
        """
        super().__init__(app, context)
        self.format_key = format_key

        # Exporter class lookup table
        self.exporter_classes = {
            "JsonTaskExporter": JsonTaskExporter,
            "CsvTaskExporter": CsvTaskExporter,
            "MarkdownTableExporter": MarkdownTableExporter,
        }

    def execute(self) -> None:
        """Execute the export command."""
        try:
            # Get all tasks (no filtering)
            result = self.context.api_client.list_tasks()
            tasks = result.tasks

            # Lookup format configuration
            format_config = EXPORT_FORMAT_CONFIG.get(self.format_key)
            if not format_config:
                self.notify_warning(f"Unknown format: {self.format_key}")
                return

            # Instantiate exporter and get extension
            exporter_class_name = format_config["exporter_class"]
            exporter_class = self.exporter_classes[exporter_class_name]
            exporter = exporter_class()  # type: ignore[abstract]
            extension = format_config["extension"]

            # Generate filename with current date
            today = DateTimeFormatter.format_date_for_filename()
            filename = f"Taskdog_export_{today}.{extension}"

            # Use ~/Downloads directory
            downloads_dir = Path.home() / "Downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)
            output_path = downloads_dir / filename

            # Export tasks
            tasks_data = exporter.export(tasks)

            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(tasks_data)

            # Show success notification
            self.notify_success(f"Exported {len(tasks)} tasks to {output_path}")

        except ServerConnectionError as e:
            self.notify_error(
                f"Server connection failed: {e.original_error.__class__.__name__}", e
            )
        except Exception as e:
            self.notify_error("Export failed", e)
