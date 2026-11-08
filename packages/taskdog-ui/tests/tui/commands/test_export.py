"""Tests for ExportCommand."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from taskdog.tui.commands.export import ExportCommand
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError


def _make_task(task_id: int) -> TaskRowDto:
    return TaskRowDto(
        id=task_id,
        name=f"Task {task_id}",
        priority=1,
        status=TaskStatus.PENDING,
        is_fixed=False,
        depends_on=[],
        tags=[],
        estimated_duration=None,
        actual_duration_hours=None,
        planned_start=None,
        planned_end=None,
        actual_start=None,
        actual_end=None,
        deadline=None,
        created_at=datetime(2024, 12, 20, 10, 0),
        updated_at=datetime(2024, 12, 20, 10, 0),
        is_archived=False,
        is_finished=False,
    )


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


class TestExportCommandExecute:
    """Test cases for execute method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.mock_context.state.is_filtered = False

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

    @patch("taskdog.tui.commands.export.create_exporter")
    @patch("taskdog.tui.commands.export.Path")
    def test_success_message_includes_task_count(
        self, mock_path: MagicMock, mock_create_exporter: MagicMock
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
        mock_create_exporter.return_value = mock_exporter

        command = ExportCommand(self.mock_app, self.mock_context, format_key="json")
        command.notify_success = MagicMock()

        with patch("builtins.open", MagicMock()):
            command.execute()

        command.notify_success.assert_called_once()
        assert "3 tasks" in command.notify_success.call_args[0][0]

    @patch("taskdog.tui.commands.export.Path")
    def test_respects_show_archived_state(self, mock_path: MagicMock) -> None:
        """Test that export passes state.show_archived to list_tasks."""
        mock_home = MagicMock()
        mock_downloads = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_downloads
        mock_downloads.__truediv__.return_value = mock_downloads

        mock_result = MagicMock()
        mock_result.tasks = []
        self.mock_context.api_client.list_tasks.return_value = mock_result
        self.mock_context.state.show_archived = True

        command = ExportCommand(self.mock_app, self.mock_context, format_key="json")
        command.notify_success = MagicMock()

        with patch("builtins.open", MagicMock()):
            command.execute()

        self.mock_context.api_client.list_tasks.assert_called_once_with(
            include_archived=True,
        )


class TestExportCommandFilter:
    """Export writes what the table shows when a search filter is active."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path) -> None:
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        result = MagicMock()
        result.tasks = [_make_task(1), _make_task(2), _make_task(3)]
        self.mock_context.api_client.list_tasks.return_value = result
        self.home = tmp_path

    def _export_ids(self) -> list[int]:
        command = ExportCommand(self.mock_app, self.mock_context, format_key="json")
        command.notify_success = MagicMock()
        command.notify_error = MagicMock()

        with patch("taskdog.tui.commands.export.Path.home", return_value=self.home):
            command.execute()

        command.notify_error.assert_not_called()
        (exported,) = (self.home / "Downloads").glob("Taskdog_export_*.json")
        return [task["id"] for task in json.loads(exported.read_text())]

    def test_exports_only_tasks_matching_active_filter(self) -> None:
        self.mock_context.state.is_filtered = True
        self.mock_context.state.filtered_task_ids = {1, 3}

        assert self._export_ids() == [1, 3]

    def test_exports_all_tasks_without_filter(self) -> None:
        self.mock_context.state.is_filtered = False

        assert self._export_ids() == [1, 2, 3]
