"""Tests for week command."""

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from taskdog.cli.commands.week import week_command


class TestWeekCommand(unittest.TestCase):
    """Test cases for week command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.week.render_table")
    def test_basic_display(self, mock_render_table):
        """Test basic week display."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_week_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(week_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.list_week_tasks.assert_called_once_with(
            all=False,
            status=None,
            sort_by="deadline",
            reverse=False,
        )
        mock_render_table.assert_called_once()

    @patch("taskdog.cli.commands.week.render_table")
    def test_with_all_option(self, mock_render_table):
        """Test week with --all option."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_week_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(week_command, ["--all"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.list_week_tasks.call_args[1]
        self.assertTrue(call_kwargs["all"])

    @patch("taskdog.cli.commands.week.render_table")
    def test_with_status_filter(self, mock_render_table):
        """Test week with --status filter."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_week_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            week_command, ["--status", "pending"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.list_week_tasks.call_args[1]
        self.assertEqual(call_kwargs["status"], "pending")

    @patch("taskdog.cli.commands.week.render_table")
    def test_with_sort_option(self, mock_render_table):
        """Test week with --sort and --reverse options."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_week_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            week_command, ["--sort", "priority", "--reverse"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.list_week_tasks.call_args[1]
        self.assertEqual(call_kwargs["sort_by"], "priority")
        self.assertTrue(call_kwargs["reverse"])

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.list_week_tasks.side_effect = error

        # Execute
        result = self.runner.invoke(week_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("displaying tasks", error)


if __name__ == "__main__":
    unittest.main()
