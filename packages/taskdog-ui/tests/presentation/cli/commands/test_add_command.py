"""Tests for add command."""

import unittest
from unittest.mock import MagicMock

from click.testing import CliRunner

from taskdog.cli.commands.add import add_command
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class TestAddCommand(unittest.TestCase):
    """Test cases for add command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_basic_add(self):
        """Test basic task creation with name only."""
        # Setup
        mock_task = MagicMock()
        mock_task.depends_on = []
        mock_task.tags = []
        self.api_client.create_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(add_command, ["Test Task"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.create_task.assert_called_once_with(
            name="Test Task",
            priority=None,
            is_fixed=False,
            tags=None,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
        )
        self.console_writer.task_success.assert_called_once_with("Added", mock_task)

    def test_add_with_priority(self):
        """Test task creation with priority."""
        # Setup
        mock_task = MagicMock()
        mock_task.depends_on = []
        mock_task.tags = []
        self.api_client.create_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            add_command, ["Test Task", "--priority", "5"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.create_task.call_args[1]
        self.assertEqual(call_kwargs["priority"], 5)

    def test_add_with_fixed_flag(self):
        """Test task creation with fixed flag."""
        # Setup
        mock_task = MagicMock()
        mock_task.depends_on = []
        mock_task.tags = []
        self.api_client.create_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            add_command, ["Test Task", "--fixed"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.create_task.call_args[1]
        self.assertTrue(call_kwargs["is_fixed"])

    def test_add_with_tags(self):
        """Test task creation with tags."""
        # Setup
        mock_task = MagicMock()
        mock_task.depends_on = []
        mock_task.tags = ["work", "urgent"]
        self.api_client.create_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            add_command,
            ["Test Task", "-t", "work", "-t", "urgent"],
            obj=self.cli_context,
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.create_task.call_args[1]
        self.assertEqual(call_kwargs["tags"], ["work", "urgent"])
        self.console_writer.info.assert_called()

    def test_add_with_deadline(self):
        """Test task creation with deadline."""
        # Setup
        mock_task = MagicMock()
        mock_task.depends_on = []
        mock_task.tags = []
        self.api_client.create_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            add_command, ["Test Task", "--deadline", "2025-12-31"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.create_task.call_args[1]
        self.assertIsNotNone(call_kwargs["deadline"])

    def test_add_with_estimate(self):
        """Test task creation with estimate."""
        # Setup
        mock_task = MagicMock()
        mock_task.depends_on = []
        mock_task.tags = []
        self.api_client.create_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            add_command, ["Test Task", "--estimate", "2.5"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.create_task.call_args[1]
        self.assertEqual(call_kwargs["estimated_duration"], 2.5)

    def test_add_with_schedule(self):
        """Test task creation with start and end times."""
        # Setup
        mock_task = MagicMock()
        mock_task.depends_on = []
        mock_task.tags = []
        self.api_client.create_task.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            add_command,
            ["Test Task", "--start", "2025-10-15", "--end", "2025-10-17"],
            obj=self.cli_context,
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.create_task.call_args[1]
        self.assertIsNotNone(call_kwargs["planned_start"])
        self.assertIsNotNone(call_kwargs["planned_end"])

    def test_add_with_dependencies(self):
        """Test task creation with dependencies."""
        # Setup
        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.depends_on = [1, 2]
        mock_task.tags = []
        self.api_client.create_task.return_value = mock_task
        self.api_client.add_dependency.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            add_command, ["Test Task", "-d", "1", "-d", "2"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(self.api_client.add_dependency.call_count, 2)
        self.console_writer.info.assert_called()

    def test_add_dependency_validation_error(self):
        """Test that dependency validation errors are handled gracefully."""
        # Setup
        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.depends_on = []
        mock_task.tags = []
        self.api_client.create_task.return_value = mock_task
        self.api_client.add_dependency.side_effect = TaskValidationError(
            "Circular dependency"
        )

        # Execute
        result = self.runner.invoke(
            add_command, ["Test Task", "-d", "1"], obj=self.cli_context
        )

        # Verify - should continue even with dependency error
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        self.console_writer.task_success.assert_called_once()

    def test_task_not_found(self):
        """Test add with non-existent task reference."""
        # Setup
        self.api_client.create_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(add_command, ["Test Task"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.create_task.side_effect = error

        # Execute
        result = self.runner.invoke(add_command, ["Test Task"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("adding task", error)

    def test_missing_name(self):
        """Test add without name argument."""
        result = self.runner.invoke(add_command, [], obj=self.cli_context)
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
