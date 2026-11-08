"""Export command for TUI."""

from pathlib import Path
from typing import TYPE_CHECKING

from taskdog.exporters import EXPORT_FILE_EXTENSIONS, create_exporter
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.context import TUIContext
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class ExportCommand(TUICommandBase):
    """Command to export tasks to various formats.

    Exports the tasks shown in the table (honoring the active search filter)
    to a file in the specified format (JSON, CSV, or Markdown).
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

    def execute(self) -> None:
        """Execute the export command."""
        try:
            extension = EXPORT_FILE_EXTENSIONS.get(self.format_key)
            if extension is None:
                self.notify_warning(f"Unknown format: {self.format_key}")
                return
            exporter = create_exporter(self.format_key)

            state = self.context.state
            result = self.context.api_client.list_tasks(
                include_archived=state.show_archived,
            )
            tasks = result.tasks

            # Export what the table shows, not every task
            if state.is_filtered:
                visible_ids = state.filtered_task_ids
                tasks = [task for task in tasks if task.id in visible_ids]

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
            with output_path.open("w", encoding="utf-8") as f:
                f.write(tasks_data)

            # Show success notification
            self.notify_success(f"Exported {len(tasks)} tasks to {output_path}")

        except ServerConnectionError as e:
            self.notify_error(
                f"Server connection failed: {e.original_error.__class__.__name__}", e
            )
        except Exception as e:
            self.notify_error("Export failed", e)
