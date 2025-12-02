"""Tests for rename command."""

import unittest
from unittest.mock import MagicMock

from click.testing import CliRunner

from taskdog.cli.commands.rename import rename_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestRenameCommand(unittest.TestCase):
    """Test cases for rename command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_success(self):
        """Test successful rename."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            rename_command, ["1", "New Task Name"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.update_task.assert_called_once_with(
            task_id=1, name="New Task Name"
        )
        self.console_writer.update_success.assert_called_once()

    def test_success_with_special_characters(self):
        """Test successful rename with special characters."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            rename_command,
            ["1", "Task with 'quotes' and \"double\""],
            obj=self.cli_context,
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.update_task.assert_called_once()

    def test_task_not_found(self):
        """Test rename with non-existent task."""
        # Setup
        self.api_client.update_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(
            rename_command, ["999", "New Name"], obj=self.cli_context
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
            rename_command, ["1", "New Name"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("renaming task", error)

    def test_missing_task_id(self):
        """Test rename without task_id argument."""
        result = self.runner.invoke(rename_command, ["New Name"], obj=self.cli_context)
        # Click shows usage error for missing argument
        self.assertNotEqual(result.exit_code, 0)

    def test_missing_name(self):
        """Test rename without name argument."""
        result = self.runner.invoke(rename_command, ["1"], obj=self.cli_context)
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
