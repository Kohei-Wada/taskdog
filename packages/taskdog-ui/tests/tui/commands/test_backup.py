"""Tests for BackupCommand."""

from unittest.mock import MagicMock, patch

import pytest

from taskdog.tui.commands.backup import BackupCommand
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError


class TestBackupCommandExecute:
    """Test cases for execute method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()

    @patch("taskdog.tui.commands.backup.Path")
    def test_downloads_backup_and_notifies_success(self, mock_path: MagicMock) -> None:
        """Backup downloads to ~/Downloads and reports success."""
        mock_home = MagicMock()
        mock_downloads = MagicMock()
        mock_output = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_downloads
        mock_downloads.__truediv__.return_value = mock_output

        command = BackupCommand(self.mock_app, self.mock_context)
        command.notify_success = MagicMock()

        command.execute()

        self.mock_context.api_client.backup.assert_called_once_with(mock_output)
        mock_downloads.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        command.notify_success.assert_called_once()

    @patch("taskdog.tui.commands.backup.Path")
    def test_filename_uses_backup_prefix_and_db_suffix(
        self, mock_path: MagicMock
    ) -> None:
        """The download filename follows taskdog-backup-<ts>.db."""
        mock_home = MagicMock()
        mock_downloads = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_downloads

        command = BackupCommand(self.mock_app, self.mock_context)
        command.notify_success = MagicMock()

        command.execute()

        filename = mock_downloads.__truediv__.call_args[0][0]
        assert filename.startswith("taskdog-backup-")
        assert filename.endswith(".db")

    def test_handles_server_connection_error(self) -> None:
        """Server connection errors are reported via notify_error."""
        original_error = ConnectionError("Connection refused")
        self.mock_context.api_client.backup.side_effect = ServerConnectionError(
            "http://localhost:8000", original_error
        )

        command = BackupCommand(self.mock_app, self.mock_context)
        command.notify_error = MagicMock()

        command.execute()

        command.notify_error.assert_called_once()
        assert "server connection" in command.notify_error.call_args[0][0].lower()

    def test_handles_generic_exception(self) -> None:
        """Generic errors are reported via notify_error."""
        self.mock_context.api_client.backup.side_effect = RuntimeError("boom")

        command = BackupCommand(self.mock_app, self.mock_context)
        command.notify_error = MagicMock()

        command.execute()

        command.notify_error.assert_called_once()
        assert "backup failed" in command.notify_error.call_args[0][0].lower()
