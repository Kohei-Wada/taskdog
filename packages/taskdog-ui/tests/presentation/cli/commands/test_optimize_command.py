"""Tests for optimize command."""

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from taskdog.cli.commands.optimize import optimize_command


class TestOptimizeCommand(unittest.TestCase):
    """Test cases for optimize command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_basic_optimize(self, mock_get_next_weekday):
        """Test basic optimization."""
        # Setup
        mock_get_next_weekday.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(optimize_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.optimize_schedule.assert_called_once()
        self.console_writer.success.assert_called_once()

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_optimize_specific_tasks(self, mock_get_next_weekday):
        """Test optimization with specific task IDs."""
        # Setup
        mock_get_next_weekday.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock(), MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["1", "2", "3"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        self.assertEqual(call_kwargs["task_ids"], [1, 2, 3])

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_optimize_with_algorithm(self, mock_get_next_weekday):
        """Test optimization with specific algorithm."""
        # Setup
        mock_get_next_weekday.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["--algorithm", "balanced"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        self.assertEqual(call_kwargs["algorithm"], "balanced")

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_optimize_with_max_hours(self, mock_get_next_weekday):
        """Test optimization with max hours per day."""
        # Setup
        mock_get_next_weekday.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["--max-hours-per-day", "8"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        self.assertEqual(call_kwargs["max_hours_per_day"], 8.0)

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_optimize_with_force(self, mock_get_next_weekday):
        """Test optimization with force flag."""
        # Setup
        mock_get_next_weekday.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(optimize_command, ["--force"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        self.assertTrue(call_kwargs["force_override"])

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_optimize_with_start_date(self, mock_get_next_weekday):
        """Test optimization with specific start date."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["--start-date", "2025-10-15"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        self.assertIsNotNone(call_kwargs["start_date"])

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_optimize_all_failed(self, mock_get_next_weekday):
        """Test optimization when all tasks fail."""
        # Setup
        mock_get_next_weekday.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.all_failed.return_value = True
        mock_result.failed_tasks = [MagicMock()]
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(optimize_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.warning.assert_called()

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_optimize_no_tasks(self, mock_get_next_weekday):
        """Test optimization when no tasks to optimize."""
        # Setup
        mock_get_next_weekday.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = []
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(optimize_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.warning.assert_called()

    @patch("taskdog.cli.commands.optimize.get_next_weekday")
    def test_optimize_partial_success(self, mock_get_next_weekday):
        """Test optimization with partial success."""
        # Setup
        mock_get_next_weekday.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = True
        mock_result.failed_tasks = [MagicMock()]
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(optimize_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.warning.assert_called()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.optimize_schedule.side_effect = error

        # Execute
        result = self.runner.invoke(optimize_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("optimizing schedules", error)


if __name__ == "__main__":
    unittest.main()
