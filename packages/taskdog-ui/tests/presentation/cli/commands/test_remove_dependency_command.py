"""Tests for remove-dependency command."""

import unittest
from unittest.mock import MagicMock

from click.testing import CliRunner

from taskdog.cli.commands.remove_dependency import remove_dependency_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestRemoveDependencyCommand(unittest.TestCase):
    """Test cases for remove-dependency command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_success(self):
        """Test successful dependency removal."""
        # Setup
        mock_task = MagicMock()
        mock_task.depends_on = []
        self.api_client.remove_dependency.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            remove_dependency_command, ["5", "3"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.remove_dependency.assert_called_once_with(5, 3)
        self.console_writer.success.assert_called_once()
        self.console_writer.info.assert_called_once()

    def test_task_not_found(self):
        """Test remove-dependency with non-existent task."""
        # Setup
        self.api_client.remove_dependency.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(
            remove_dependency_command, ["999", "3"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Dependency not found")
        self.api_client.remove_dependency.side_effect = error

        # Execute
        result = self.runner.invoke(
            remove_dependency_command, ["5", "3"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("removing dependency", error)

    def test_missing_task_id(self):
        """Test remove-dependency without task_id argument."""
        result = self.runner.invoke(
            remove_dependency_command, ["3"], obj=self.cli_context
        )
        self.assertNotEqual(result.exit_code, 0)

    def test_missing_depends_on_id(self):
        """Test remove-dependency without depends_on_id argument."""
        result = self.runner.invoke(
            remove_dependency_command, ["5"], obj=self.cli_context
        )
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
