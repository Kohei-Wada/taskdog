"""Tests for estimate command."""

import unittest
from unittest.mock import MagicMock

from click.testing import CliRunner

from taskdog.cli.commands.estimate import estimate_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestEstimateCommand(unittest.TestCase):
    """Test cases for estimate command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_success(self):
        """Test successful estimate update."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            estimate_command, ["1", "2.5"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.update_task.assert_called_once_with(
            task_id=1, estimated_duration=2.5
        )
        self.console_writer.update_success.assert_called_once()

    def test_success_integer_value(self):
        """Test successful estimate update with integer value."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(estimate_command, ["1", "8"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.update_task.assert_called_once_with(
            task_id=1, estimated_duration=8.0
        )

    def test_formatter_callback(self):
        """Test that update_success is called with formatter callback."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            estimate_command, ["1", "2.5"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        # Check that update_success was called with a formatter
        call_args = self.console_writer.update_success.call_args
        self.assertEqual(call_args[0][0], mock_task)
        self.assertEqual(call_args[0][1], "estimated duration")
        self.assertEqual(call_args[0][2], 2.5)
        # Fourth argument should be the formatter callable
        formatter = call_args[0][3]
        self.assertEqual(formatter(2.5), "2.5h")

    def test_task_not_found(self):
        """Test estimate with non-existent task."""
        # Setup
        self.api_client.update_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(
            estimate_command, ["999", "2.5"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.update_task.side_effect = error

        # Execute
        result = self.runner.invoke(
            estimate_command, ["1", "2.5"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("setting estimate", error)

    def test_missing_task_id(self):
        """Test estimate without task_id argument."""
        result = self.runner.invoke(estimate_command, ["2.5"], obj=self.cli_context)
        # Click shows usage error for missing argument
        self.assertNotEqual(result.exit_code, 0)

    def test_missing_hours(self):
        """Test estimate without hours argument."""
        result = self.runner.invoke(estimate_command, ["1"], obj=self.cli_context)
        self.assertNotEqual(result.exit_code, 0)

    def test_zero_hours_rejected(self):
        """Test that zero hours is rejected by PositiveFloat."""
        result = self.runner.invoke(estimate_command, ["1", "0"], obj=self.cli_context)
        self.assertNotEqual(result.exit_code, 0)

    def test_negative_hours_rejected(self):
        """Test that negative hours is rejected by PositiveFloat."""
        result = self.runner.invoke(
            estimate_command, ["1", "-1.5"], obj=self.cli_context
        )
        self.assertNotEqual(result.exit_code, 0)

    def test_non_numeric_hours_rejected(self):
        """Test that non-numeric hours is rejected."""
        result = self.runner.invoke(
            estimate_command, ["1", "abc"], obj=self.cli_context
        )
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
