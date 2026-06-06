"""Backup command for TUI."""

from pathlib import Path

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.commands.base import TUICommandBase
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError


class BackupCommand(TUICommandBase):
    """Command to back up the database to a physical snapshot file.

    Downloads a consistent `.db` snapshot from the server into ~/Downloads.
    """

    def execute(self) -> None:
        """Execute the backup command."""
        timestamp = DateTimeFormatter.format_timestamp_for_filename()
        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        output_path = downloads_dir / f"taskdog-backup-{timestamp}.db"

        try:
            self.context.api_client.backup(output_path)
            self.notify_success(f"Backup saved to {output_path}")
        except ServerConnectionError as e:
            self.notify_error(
                f"Server connection failed: {e.original_error.__class__.__name__}", e
            )
        except Exception as e:
            self.notify_error("Backup failed", e)
