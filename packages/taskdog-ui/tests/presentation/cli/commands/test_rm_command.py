"""Tests for rm command."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.rm import rm_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestRmCommand:
    """Test cases for rm command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_single_task_archive_default(self):
        """Test archiving a single task (default behavior)."""
        # Setup
        mock_task = MagicMock()
        mock_task.id = 1
        self.api_client.archive_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(rm_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.archive_task.assert_called_once_with(1)
        self.api_client.remove_task.assert_not_called()
        self.console_writer.task_success.assert_called_once()
        self.console_writer.info.assert_called_once()

    def test_single_task_hard_delete(self):
        """Test hard deleting a single task."""
        # Setup - no return value for hard delete
        self.api_client.remove_task.return_value = None

        # Execute
        result = self.runner.invoke(rm_command, ["1", "--hard"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.remove_task.assert_called_once_with(1)
        self.api_client.archive_task.assert_not_called()
        self.console_writer.success.assert_called_once()

    def test_multiple_tasks_archive(self):
        """Test archiving multiple tasks."""
        # Setup
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task2 = MagicMock()
        mock_task2.id = 2
        self.api_client.archive_task.side_effect = [mock_task1, mock_task2]

        # Execute
        result = self.runner.invoke(rm_command, ["1", "2"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        assert self.api_client.archive_task.call_count == 2
        assert self.console_writer.task_success.call_count == 2
        # Spacing added for multiple tasks
        assert self.console_writer.empty_line.call_count == 2

    def test_multiple_tasks_hard_delete(self):
        """Test hard deleting multiple tasks."""
        # Setup
        self.api_client.remove_task.return_value = None

        # Execute
        result = self.runner.invoke(
            rm_command, ["1", "2", "--hard"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        assert self.api_client.remove_task.call_count == 2
        assert self.console_writer.success.call_count == 2

    def test_task_not_found_archive(self):
        """Test archive with non-existent task."""
        # Setup
        self.api_client.archive_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(rm_command, ["999"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_task_not_found_hard_delete(self):
        """Test hard delete with non-existent task."""
        # Setup
        self.api_client.remove_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(rm_command, ["999", "--hard"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.archive_task.side_effect = error

        # Execute
        result = self.runner.invoke(rm_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("removing task", error)

    def test_no_task_id_provided(self):
        """Test rm without providing task ID."""
        result = self.runner.invoke(rm_command, [], obj=self.cli_context)
        assert result.exit_code != 0
