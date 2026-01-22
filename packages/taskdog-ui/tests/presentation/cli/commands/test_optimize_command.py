"""Tests for optimize command."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.optimize import optimize_command


class TestOptimizeCommand:
    """Test cases for optimize command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_basic_optimize(self):
        """Test basic optimization."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["-a", "greedy"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.optimize_schedule.assert_called_once()
        self.console_writer.success.assert_called_once()

    def test_optimize_specific_tasks(self):
        """Test optimization with specific task IDs."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock(), MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["-a", "greedy", "1", "2", "3"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        assert call_kwargs["task_ids"] == [1, 2, 3]

    def test_optimize_with_algorithm(self):
        """Test optimization with specific algorithm."""
        # Setup
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
        assert result.exit_code == 0
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        assert call_kwargs["algorithm"] == "balanced"

    def test_optimize_with_max_hours(self):
        """Test optimization with max hours per day."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command,
            ["-a", "greedy", "--max-hours-per-day", "8"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        assert call_kwargs["max_hours_per_day"] == 8.0

    def test_optimize_with_force(self):
        """Test optimization with force flag."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["-a", "greedy", "--force"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        assert call_kwargs["force_override"] is True

    def test_optimize_with_start_date(self):
        """Test optimization with specific start date."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command,
            ["-a", "greedy", "--start-date", "2025-10-15"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        assert call_kwargs["start_date"] is not None

    def test_optimize_without_start_date(self):
        """Test optimization without start date passes None to API."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = False
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["-a", "greedy"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.optimize_schedule.call_args[1]
        assert call_kwargs["start_date"] is None

    def test_optimize_all_failed(self):
        """Test optimization when all tasks fail."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = True
        mock_result.failed_tasks = [MagicMock()]
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["-a", "greedy"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.warning.assert_called()

    def test_optimize_no_tasks(self):
        """Test optimization when no tasks to optimize."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = []
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["-a", "greedy"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.warning.assert_called()

    def test_optimize_partial_success(self):
        """Test optimization with partial success."""
        # Setup
        mock_result = MagicMock()
        mock_result.all_failed.return_value = False
        mock_result.successful_tasks = [MagicMock()]
        mock_result.has_failures.return_value = True
        mock_result.failed_tasks = [MagicMock()]
        self.api_client.optimize_schedule.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            optimize_command, ["-a", "greedy"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.warning.assert_called()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.optimize_schedule.side_effect = error

        # Execute
        result = self.runner.invoke(
            optimize_command, ["-a", "greedy"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("optimizing schedules", error)

    def test_missing_algorithm_fails(self):
        """Test that missing algorithm option causes error."""
        # Execute without -a option
        result = self.runner.invoke(optimize_command, [], obj=self.cli_context)

        # Verify - should fail with missing required option
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()
