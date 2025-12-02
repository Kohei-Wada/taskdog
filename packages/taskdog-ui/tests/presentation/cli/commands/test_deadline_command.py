"""Tests for deadline command."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.deadline import deadline_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestDeadlineCommand:
    """Test cases for deadline command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_success(self):
        """Test successful deadline update."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            deadline_command, ["1", "2025-12-31"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.update_task.assert_called_once()
        call_kwargs = self.api_client.update_task.call_args[1]
        assert call_kwargs["task_id"] == 1
        assert isinstance(call_kwargs["deadline"], datetime)
        self.console_writer.update_success.assert_called_once()

    def test_success_with_time(self):
        """Test successful deadline update with time specified."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            deadline_command, ["1", "2025-12-31 23:59:59"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.update_task.call_args[1]
        assert isinstance(call_kwargs["deadline"], datetime)

    def test_task_not_found(self):
        """Test deadline with non-existent task."""
        # Setup
        self.api_client.update_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(
            deadline_command, ["999", "2025-12-31"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.update_task.side_effect = error

        # Execute
        result = self.runner.invoke(
            deadline_command, ["1", "2025-12-31"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("setting deadline", error)

    def test_missing_task_id(self):
        """Test deadline without task_id argument."""
        result = self.runner.invoke(
            deadline_command, ["2025-12-31"], obj=self.cli_context
        )
        # Click shows usage error for missing argument
        assert result.exit_code != 0

    def test_missing_deadline(self):
        """Test deadline without deadline argument."""
        result = self.runner.invoke(deadline_command, ["1"], obj=self.cli_context)
        assert result.exit_code != 0

    def test_invalid_date_format(self):
        """Test deadline with invalid date format."""
        result = self.runner.invoke(
            deadline_command, ["1", "invalid-date"], obj=self.cli_context
        )
        assert result.exit_code != 0
