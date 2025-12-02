"""Tests for log-hours command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.log_hours import log_hours_command
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class TestLogHoursCommand:
    """Test cases for log-hours command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.log_hours.DateTimeFormatter")
    def test_basic_log_hours(self, mock_formatter):
        """Test logging hours with default date (today)."""
        # Setup
        mock_formatter.format_date_only.return_value = "2025-01-15"
        mock_task = MagicMock()
        mock_task.actual_daily_hours = {"2025-01-15": 3.5}
        self.api_client.log_hours.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            log_hours_command, ["5", "3.5"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.log_hours.assert_called_once_with(5, 3.5, "2025-01-15")
        self.console_writer.success.assert_called_once()
        self.console_writer.info.assert_called_once()

    def test_log_hours_with_date(self):
        """Test logging hours with specific date."""
        # Setup
        mock_task = MagicMock()
        mock_task.actual_daily_hours = {"2025-01-10": 4.0}
        self.api_client.log_hours.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            log_hours_command,
            ["5", "4.0", "--date", "2025-01-10"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.log_hours.assert_called_once_with(5, 4.0, "2025-01-10")

    def test_log_hours_with_short_date_option(self):
        """Test logging hours with -d short option."""
        # Setup
        mock_task = MagicMock()
        mock_task.actual_daily_hours = {"2025-01-12": 2.5}
        self.api_client.log_hours.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            log_hours_command, ["5", "2.5", "-d", "2025-01-12"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.log_hours.assert_called_once_with(5, 2.5, "2025-01-12")

    def test_log_hours_multiple_entries(self):
        """Test logging hours shows total accumulated hours."""
        # Setup
        mock_task = MagicMock()
        mock_task.actual_daily_hours = {
            "2025-01-10": 4.0,
            "2025-01-11": 3.0,
            "2025-01-12": 2.5,
        }
        self.api_client.log_hours.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            log_hours_command, ["5", "2.5", "-d", "2025-01-12"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        # Check that info message includes total hours (4.0 + 3.0 + 2.5 = 9.5)
        self.console_writer.info.assert_called_once()
        call_args = self.console_writer.info.call_args[0][0]
        assert "9.5" in call_args

    def test_task_not_found(self):
        """Test log-hours with non-existent task."""
        # Setup
        self.api_client.log_hours.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(
            log_hours_command, ["999", "3.5"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    @patch("taskdog.cli.commands.log_hours.DateTimeFormatter")
    def test_validation_error(self, mock_formatter):
        """Test log-hours with validation error."""
        # Setup
        mock_formatter.format_date_only.return_value = "2025-01-15"
        self.api_client.log_hours.side_effect = TaskValidationError(
            "Hours must be positive"
        )

        # Execute
        result = self.runner.invoke(log_hours_command, ["5", "0"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.log_hours.side_effect = error

        # Execute
        result = self.runner.invoke(
            log_hours_command, ["5", "3.5"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("logging hours", error)

    def test_missing_task_id(self):
        """Test log-hours without task_id argument."""
        result = self.runner.invoke(log_hours_command, ["3.5"], obj=self.cli_context)
        assert result.exit_code != 0

    def test_missing_hours(self):
        """Test log-hours without hours argument."""
        result = self.runner.invoke(log_hours_command, ["5"], obj=self.cli_context)
        assert result.exit_code != 0
