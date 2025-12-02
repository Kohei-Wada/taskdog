"""Tests for priority command."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.priority import priority_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestPriorityCommand:
    """Test cases for priority command."""

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
        """Test successful priority update."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(priority_command, ["1", "5"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.update_task.assert_called_once_with(task_id=1, priority=5)
        self.console_writer.update_success.assert_called_once()

    def test_task_not_found(self):
        """Test priority with non-existent task."""
        # Setup
        self.api_client.update_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(
            priority_command, ["999", "5"], obj=self.cli_context
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
        result = self.runner.invoke(priority_command, ["1", "5"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("setting priority", error)

    def test_missing_task_id(self):
        """Test priority without task_id argument."""
        result = self.runner.invoke(priority_command, ["5"], obj=self.cli_context)
        # Click shows usage error for missing argument
        assert result.exit_code != 0

    def test_missing_priority(self):
        """Test priority without priority argument."""
        result = self.runner.invoke(priority_command, ["1"], obj=self.cli_context)
        assert result.exit_code != 0

    def test_zero_priority_rejected(self):
        """Test that zero priority is rejected by PositiveInt."""
        result = self.runner.invoke(priority_command, ["1", "0"], obj=self.cli_context)
        assert result.exit_code != 0

    def test_negative_priority_rejected(self):
        """Test that negative priority is rejected by PositiveInt."""
        result = self.runner.invoke(priority_command, ["1", "-1"], obj=self.cli_context)
        assert result.exit_code != 0

    def test_non_integer_priority_rejected(self):
        """Test that non-integer priority is rejected."""
        result = self.runner.invoke(
            priority_command, ["1", "abc"], obj=self.cli_context
        )
        assert result.exit_code != 0
