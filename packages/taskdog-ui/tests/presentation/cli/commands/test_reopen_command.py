"""Tests for reopen command."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.reopen import reopen_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_core.shared.constants import StatusVerbs


class TestReopenCommand:
    """Test cases for reopen command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_single_task_success(self):
        """Test successful reopen of a single task."""
        # Setup
        mock_task = MagicMock()
        self.api_client.reopen_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(reopen_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.reopen_task.assert_called_once_with(1)
        self.console_writer.task_success.assert_called_once_with(
            StatusVerbs.REOPENED, mock_task
        )

    def test_multiple_tasks_success(self):
        """Test successful reopen of multiple tasks."""
        # Setup
        mock_task1 = MagicMock()
        mock_task2 = MagicMock()
        self.api_client.reopen_task.side_effect = [mock_task1, mock_task2]

        # Execute
        result = self.runner.invoke(reopen_command, ["1", "2"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        assert self.api_client.reopen_task.call_count == 2
        assert self.console_writer.task_success.call_count == 2
        # Spacing added for multiple tasks
        assert self.console_writer.empty_line.call_count == 2

    def test_task_not_found(self):
        """Test reopen with non-existent task."""
        # Setup
        self.api_client.reopen_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(reopen_command, ["999"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.reopen_task.side_effect = error

        # Execute
        result = self.runner.invoke(reopen_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("reopening task", error)

    def test_no_task_id_provided(self):
        """Test reopen without providing task ID."""
        result = self.runner.invoke(reopen_command, [], obj=self.cli_context)
        assert result.exit_code != 0
