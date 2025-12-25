"""Tests for fix-actual command."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.fix_actual import fix_actual_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestFixActualCommand:
    """Test cases for fix-actual command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @pytest.mark.parametrize(
        "args,expected_kwargs",
        [
            # Single field updates
            (
                ["1", "--start", "2025-12-13 09:00:00"],
                {
                    "task_id": 1,
                    "actual_start": datetime(2025, 12, 13, 9, 0, 0),
                    "actual_end": None,
                    "actual_duration": None,
                    "clear_start": False,
                    "clear_end": False,
                    "clear_duration": False,
                },
            ),
            (
                ["1", "--end", "2025-12-13 17:00:00"],
                {
                    "task_id": 1,
                    "actual_start": None,
                    "actual_end": datetime(2025, 12, 13, 17, 0, 0),
                    "actual_duration": None,
                    "clear_start": False,
                    "clear_end": False,
                    "clear_duration": False,
                },
            ),
            (
                ["1", "--duration", "8.5"],
                {
                    "task_id": 1,
                    "actual_start": None,
                    "actual_end": None,
                    "actual_duration": 8.5,
                    "clear_start": False,
                    "clear_end": False,
                    "clear_duration": False,
                },
            ),
            # Multiple fields
            (
                ["1", "--start", "2025-12-13 09:00:00", "--end", "2025-12-13 17:00:00"],
                {
                    "task_id": 1,
                    "actual_start": datetime(2025, 12, 13, 9, 0, 0),
                    "actual_end": datetime(2025, 12, 13, 17, 0, 0),
                    "actual_duration": None,
                    "clear_start": False,
                    "clear_end": False,
                    "clear_duration": False,
                },
            ),
            (
                [
                    "1",
                    "--start",
                    "2025-12-13 09:00:00",
                    "--end",
                    "2025-12-15 17:00:00",
                    "--duration",
                    "16",
                ],
                {
                    "task_id": 1,
                    "actual_start": datetime(2025, 12, 13, 9, 0, 0),
                    "actual_end": datetime(2025, 12, 15, 17, 0, 0),
                    "actual_duration": 16.0,
                    "clear_start": False,
                    "clear_end": False,
                    "clear_duration": False,
                },
            ),
            # Short options
            (
                [
                    "1",
                    "-s",
                    "2025-12-13 09:00:00",
                    "-e",
                    "2025-12-13 17:00:00",
                    "-d",
                    "8",
                ],
                {
                    "task_id": 1,
                    "actual_start": datetime(2025, 12, 13, 9, 0, 0),
                    "actual_end": datetime(2025, 12, 13, 17, 0, 0),
                    "actual_duration": 8.0,
                    "clear_start": False,
                    "clear_end": False,
                    "clear_duration": False,
                },
            ),
            # Date-only input (defaults to specific times)
            (
                ["1", "--start", "2025-12-13"],
                {
                    "task_id": 1,
                    "actual_start": datetime(2025, 12, 13, 9, 0, 0),
                    "actual_end": None,
                    "actual_duration": None,
                    "clear_start": False,
                    "clear_end": False,
                    "clear_duration": False,
                },
            ),
            (
                ["1", "--end", "2025-12-13"],
                {
                    "task_id": 1,
                    "actual_start": None,
                    "actual_end": datetime(2025, 12, 13, 18, 0, 0),
                    "actual_duration": None,
                    "clear_start": False,
                    "clear_end": False,
                    "clear_duration": False,
                },
            ),
        ],
        ids=[
            "start_only",
            "end_only",
            "duration_only",
            "start_and_end",
            "all_options",
            "short_options",
            "date_only_start",
            "date_only_end",
        ],
    )
    def test_fix_actual_success(self, args, expected_kwargs):
        """Test successful fix-actual operations."""
        result = self.runner.invoke(fix_actual_command, args, obj=self.cli_context)

        assert result.exit_code == 0
        self.api_client.fix_actual_times.assert_called_once_with(**expected_kwargs)
        self.console_writer.success.assert_called_once()

    @pytest.mark.parametrize(
        "args,expected_clear",
        [
            (["1", "--start", ""], {"clear_start": True}),
            (["1", "--end", ""], {"clear_end": True}),
            (["1", "--duration", ""], {"clear_duration": True}),
        ],
        ids=["clear_start", "clear_end", "clear_duration"],
    )
    def test_clear_operations(self, args, expected_clear):
        """Test clearing actual values."""
        result = self.runner.invoke(fix_actual_command, args, obj=self.cli_context)

        assert result.exit_code == 0
        call_kwargs = self.api_client.fix_actual_times.call_args[1]
        for key, value in expected_clear.items():
            assert call_kwargs[key] == value

    @pytest.mark.parametrize(
        "args,error_message",
        [
            (["1"], "At least one of --start, --end, or --duration is required"),
            (["1", "--duration", "-5"], "Duration must be greater than 0"),
            (["1", "--duration", "0"], "Duration must be greater than 0"),
        ],
        ids=["no_options", "negative_duration", "zero_duration"],
    )
    def test_validation_errors(self, args, error_message):
        """Test validation error cases."""
        self.runner.invoke(fix_actual_command, args, obj=self.cli_context)

        self.console_writer.validation_error.assert_called_once_with(error_message)
        self.api_client.fix_actual_times.assert_not_called()

    def test_end_before_start_error(self):
        """Test error when end is before start."""
        self.runner.invoke(
            fix_actual_command,
            ["1", "--start", "2025-12-13 17:00:00", "--end", "2025-12-13 09:00:00"],
            obj=self.cli_context,
        )

        self.console_writer.validation_error.assert_called_once()
        assert "cannot be before start time" in str(
            self.console_writer.validation_error.call_args
        )
        self.api_client.fix_actual_times.assert_not_called()

    def test_task_not_found(self):
        """Test fix-actual with non-existent task."""
        self.api_client.fix_actual_times.side_effect = TaskNotFoundException(999)

        result = self.runner.invoke(
            fix_actual_command,
            ["999", "--start", "2025-12-13 09:00:00"],
            obj=self.cli_context,
        )

        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        error = ValueError("Something went wrong")
        self.api_client.fix_actual_times.side_effect = error

        result = self.runner.invoke(
            fix_actual_command,
            ["1", "--start", "2025-12-13 09:00:00"],
            obj=self.cli_context,
        )

        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("fixing actual times", error)

    def test_missing_task_id(self):
        """Test fix-actual without task_id argument."""
        result = self.runner.invoke(fix_actual_command, [], obj=self.cli_context)
        assert result.exit_code != 0

    def test_invalid_duration_format(self):
        """Test error with invalid duration format."""
        result = self.runner.invoke(
            fix_actual_command,
            ["1", "--duration", "abc"],
            obj=self.cli_context,
        )

        assert result.exit_code != 0
        assert "not a valid float" in result.output
