"""Tests for today command."""

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from taskdog.cli.commands.today import today_command


class TestTodayCommand(unittest.TestCase):
    """Test cases for today command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.today.render_table")
    def test_basic_display(self, mock_render_table):
        """Test basic today display."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_today_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(today_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.api_client.list_today_tasks.assert_called_once_with(
            all=False,
            status=None,
            sort_by="deadline",
            reverse=False,
        )
        mock_render_table.assert_called_once()

    @patch("taskdog.cli.commands.today.render_table")
    def test_with_all_option(self, mock_render_table):
        """Test today with --all option."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_today_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(today_command, ["--all"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.list_today_tasks.call_args[1]
        self.assertTrue(call_kwargs["all"])

    @patch("taskdog.cli.commands.today.render_table")
    def test_with_status_filter(self, mock_render_table):
        """Test today with --status filter."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_today_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            today_command, ["--status", "pending"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.list_today_tasks.call_args[1]
        self.assertEqual(call_kwargs["status"], "pending")

    @patch("taskdog.cli.commands.today.render_table")
    def test_with_sort_option(self, mock_render_table):
        """Test today with --sort and --reverse options."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_today_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            today_command, ["--sort", "priority", "--reverse"], obj=self.cli_context
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.api_client.list_today_tasks.call_args[1]
        self.assertEqual(call_kwargs["sort_by"], "priority")
        self.assertTrue(call_kwargs["reverse"])

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.list_today_tasks.side_effect = error

        # Execute
        result = self.runner.invoke(today_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("displaying tasks", error)


if __name__ == "__main__":
    unittest.main()
