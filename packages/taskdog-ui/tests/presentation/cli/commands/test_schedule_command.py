"""Tests for schedule command."""

import unittest
from unittest.mock import MagicMock

from click.testing import CliRunner

from taskdog.cli.commands.schedule import schedule_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestScheduleCommand(unittest.TestCase):
    """Test cases for schedule command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_schedule_start_only(self):
        """Test setting only start date."""
        # Setup
        mock_task = MagicMock()
        mock_task.planned_start = "2025-10-15"
        mock_task.planned_end = None
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            schedule_command, ["1", "2025-10-15"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.update_task.call_args[1]
        self.assertIsNotNone(call_kwargs["planned_start"])
        self.assertIsNone(call_kwargs["planned_end"])
        self.console_writer.update_success.assert_called_once()

    def test_schedule_start_and_end(self):
        """Test setting both start and end dates."""
        # Setup
        mock_task = MagicMock()
        mock_task.planned_start = "2025-10-15"
        mock_task.planned_end = "2025-10-17"
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            schedule_command, ["1", "2025-10-15", "2025-10-17"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.update_task.call_args[1]
        self.assertIsNotNone(call_kwargs["planned_start"])
        self.assertIsNotNone(call_kwargs["planned_end"])

    def test_schedule_with_time(self):
        """Test setting dates with specific times."""
        # Setup
        mock_task = MagicMock()
        mock_task.planned_start = "2025-10-15 09:00:00"
        mock_task.planned_end = "2025-10-17 18:00:00"
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            schedule_command,
            ["1", "2025-10-15 09:00:00", "2025-10-17 18:00:00"],
            obj=self.cli_context,
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.update_task.call_args[1]
        self.assertIsNotNone(call_kwargs["planned_start"])
        self.assertIsNotNone(call_kwargs["planned_end"])

    def test_task_not_found(self):
        """Test schedule with non-existent task."""
        # Setup
        self.api_client.update_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(
            schedule_command, ["999", "2025-10-15"], obj=self.cli_context
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
            schedule_command, ["1", "2025-10-15"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("setting schedule", error)

    def test_missing_task_id(self):
        """Test schedule without task_id argument."""
        result = self.runner.invoke(
            schedule_command, ["2025-10-15"], obj=self.cli_context
        )
        self.assertNotEqual(result.exit_code, 0)

    def test_missing_start(self):
        """Test schedule without start argument."""
        result = self.runner.invoke(schedule_command, ["1"], obj=self.cli_context)
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
