"""Tests for restore command."""

import unittest
from unittest.mock import MagicMock

from click.testing import CliRunner

from taskdog.cli.commands.restore import restore_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_core.shared.constants import StatusVerbs


class TestRestoreCommand(unittest.TestCase):
    """Test cases for restore command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_single_task_success(self):
        """Test successful restore of a single task."""
        # Setup
        mock_task = MagicMock()
        self.api_client.restore_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(restore_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.restore_task.assert_called_once_with(1)
        self.console_writer.task_success.assert_called_once_with(
            StatusVerbs.RESTORED, mock_task
        )

    def test_multiple_tasks_success(self):
        """Test successful restore of multiple tasks."""
        # Setup
        mock_task1 = MagicMock()
        mock_task2 = MagicMock()
        self.api_client.restore_task.side_effect = [mock_task1, mock_task2]

        # Execute
        result = self.runner.invoke(restore_command, ["1", "2"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(self.api_client.restore_task.call_count, 2)
        self.assertEqual(self.console_writer.task_success.call_count, 2)
        # Spacing added for multiple tasks
        self.assertEqual(self.console_writer.empty_line.call_count, 2)

    def test_task_not_found(self):
        """Test restore with non-existent task."""
        # Setup
        self.api_client.restore_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(restore_command, ["999"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.restore_task.side_effect = error

        # Execute
        result = self.runner.invoke(restore_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("restoring task", error)

    def test_no_task_id_provided(self):
        """Test restore without providing task ID."""
        result = self.runner.invoke(restore_command, [], obj=self.cli_context)
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
