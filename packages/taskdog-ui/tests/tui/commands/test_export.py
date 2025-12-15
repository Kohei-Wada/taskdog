"""Tests for ExportCommand."""

from unittest.mock import MagicMock, patch

import pytest

from taskdog.tui.commands.export import ExportCommand
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError


class TestExportCommandInit:
    """Test cases for ExportCommand initialization."""

    def test_stores_format_key(self) -> None:
        """Test that format key is stored correctly."""
        mock_app = MagicMock()
        mock_context = MagicMock()

        command = ExportCommand(mock_app, mock_context, format_key="json")

        assert command.format_key == "json"

    def test_default_format_key_is_empty(self) -> None:
        """Test that default format key is empty string."""
        mock_app = MagicMock()
        mock_context = MagicMock()

        command = ExportCommand(mock_app, mock_context)

        assert command.format_key == ""

    def test_exporter_classes_registered(self) -> None:
        """Test that exporter classes are registered."""
        mock_app = MagicMock()
        mock_context = MagicMock()

        command = ExportCommand(mock_app, mock_context)

        assert "JsonTaskExporter" in command.exporter_classes
        assert "CsvTaskExporter" in command.exporter_classes
        assert "MarkdownTableExporter" in command.exporter_classes


class TestExportCommandExecute:
    """Test cases for execute method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()

    def test_warns_on_unknown_format(self) -> None:
        """Test warning when format is unknown."""
        command = ExportCommand(self.mock_app, self.mock_context, format_key="unknown")
        command.notify_warning = MagicMock()

        command.execute()

        command.notify_warning.assert_called_once()
        assert "unknown" in command.notify_warning.call_args[0][0].lower()

    @patch("taskdog.tui.commands.export.Path")
    def test_exports_json_format(self, mock_path: MagicMock) -> None:
        """Test JSON format export."""
        mock_home = MagicMock()
        mock_downloads = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_downloads
        mock_downloads.__truediv__.return_value = mock_downloads

        mock_result = MagicMock()
        mock_result.tasks = []
        self.mock_context.api_client.list_tasks.return_value = mock_result

        command = ExportCommand(self.mock_app, self.mock_context, format_key="json")
        command.notify_success = MagicMock()

        with patch("builtins.open", MagicMock()):
            command.execute()

        command.notify_success.assert_called_once()

    @patch("taskdog.tui.commands.export.Path")
    def test_exports_csv_format(self, mock_path: MagicMock) -> None:
        """Test CSV format export."""
        mock_home = MagicMock()
        mock_downloads = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_downloads
        mock_downloads.__truediv__.return_value = mock_downloads

        mock_result = MagicMock()
        mock_result.tasks = []
        self.mock_context.api_client.list_tasks.return_value = mock_result

        command = ExportCommand(self.mock_app, self.mock_context, format_key="csv")
        command.notify_success = MagicMock()

        with patch("builtins.open", MagicMock()):
            command.execute()

        command.notify_success.assert_called_once()

    @patch("taskdog.tui.commands.export.Path")
    def test_exports_markdown_format(self, mock_path: MagicMock) -> None:
        """Test Markdown format export."""
        mock_home = MagicMock()
        mock_downloads = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_downloads
        mock_downloads.__truediv__.return_value = mock_downloads

        mock_result = MagicMock()
        mock_result.tasks = []
        self.mock_context.api_client.list_tasks.return_value = mock_result

        command = ExportCommand(self.mock_app, self.mock_context, format_key="markdown")
        command.notify_success = MagicMock()

        with patch("builtins.open", MagicMock()):
            command.execute()

        command.notify_success.assert_called_once()

    def test_handles_server_connection_error(self) -> None:
        """Test handling of server connection error."""
        original_error = ConnectionError("Connection refused")
        self.mock_context.api_client.list_tasks.side_effect = ServerConnectionError(
            "http://localhost:8000", original_error
        )

        command = ExportCommand(self.mock_app, self.mock_context, format_key="json")
        command.notify_error = MagicMock()

        command.execute()

        command.notify_error.assert_called_once()
        assert "server connection" in command.notify_error.call_args[0][0].lower()

    def test_handles_generic_exception(self) -> None:
        """Test handling of generic exceptions."""
        self.mock_context.api_client.list_tasks.side_effect = RuntimeError(
            "Unexpected error"
        )

        command = ExportCommand(self.mock_app, self.mock_context, format_key="json")
        command.notify_error = MagicMock()

        command.execute()

        command.notify_error.assert_called_once()
        assert "export failed" in command.notify_error.call_args[0][0].lower()

    @patch("taskdog.tui.commands.export.Path")
    def test_creates_downloads_directory(self, mock_path: MagicMock) -> None:
        """Test that Downloads directory is created if it doesn't exist."""
        mock_home = MagicMock()
        mock_downloads = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_downloads
        mock_downloads.__truediv__.return_value = mock_downloads

        mock_result = MagicMock()
        mock_result.tasks = []
        self.mock_context.api_client.list_tasks.return_value = mock_result

        command = ExportCommand(self.mock_app, self.mock_context, format_key="json")
        command.notify_success = MagicMock()

        with patch("builtins.open", MagicMock()):
            command.execute()

        mock_downloads.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("taskdog.tui.commands.export.JsonTaskExporter")
    @patch("taskdog.tui.commands.export.Path")
    def test_success_message_includes_task_count(
        self, mock_path: MagicMock, mock_exporter_class: MagicMock
    ) -> None:
        """Test that success message includes task count."""
        mock_home = MagicMock()
        mock_downloads = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_downloads
        mock_downloads.__truediv__.return_value = mock_downloads

        mock_result = MagicMock()
        mock_result.tasks = [MagicMock(), MagicMock(), MagicMock()]  # 3 tasks
        self.mock_context.api_client.list_tasks.return_value = mock_result

        # Mock the exporter instance
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = "[]"
        mock_exporter_class.return_value = mock_exporter

        command = ExportCommand(self.mock_app, self.mock_context, format_key="json")
        # Re-assign to use the mock
        command.exporter_classes["JsonTaskExporter"] = mock_exporter_class
        command.notify_success = MagicMock()

        with patch("builtins.open", MagicMock()):
            command.execute()

        command.notify_success.assert_called_once()
        assert "3 tasks" in command.notify_success.call_args[0][0]
