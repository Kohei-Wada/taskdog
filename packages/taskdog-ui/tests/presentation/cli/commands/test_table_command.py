"""Tests for table command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.table import table_command


class TestTableCommand:
    """Test cases for table command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.table.render_table")
    def test_basic_display(self, mock_render_table):
        """Test basic table display."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(table_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.list_tasks.assert_called_once_with(
            all=False,
            status=None,
            tags=None,
            start_date=None,
            end_date=None,
            sort_by="id",
            reverse=False,
        )
        mock_render_table.assert_called_once()

    @patch("taskdog.cli.commands.table.render_table")
    def test_with_all_option(self, mock_render_table):
        """Test table with --all option."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(table_command, ["--all"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.list_tasks.call_args[1]
        assert call_kwargs["all"] is True

    @patch("taskdog.cli.commands.table.render_table")
    def test_with_status_filter(self, mock_render_table):
        """Test table with --status filter."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            table_command, ["--status", "completed"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.list_tasks.call_args[1]
        assert call_kwargs["status"] == "completed"

    @patch("taskdog.cli.commands.table.render_table")
    def test_with_tags_filter(self, mock_render_table):
        """Test table with --tag filter (multiple tags)."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            table_command, ["-t", "work", "-t", "urgent"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.list_tasks.call_args[1]
        assert call_kwargs["tags"] == ["work", "urgent"]

    @patch("taskdog.cli.commands.table.render_table")
    def test_with_sort_option(self, mock_render_table):
        """Test table with --sort and --reverse options."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            table_command, ["--sort", "priority", "--reverse"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.list_tasks.call_args[1]
        assert call_kwargs["sort_by"] == "priority"
        assert call_kwargs["reverse"] is True

    @patch("taskdog.cli.commands.table.render_table")
    def test_with_fields_option(self, mock_render_table):
        """Test table with --fields option."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            table_command, ["--fields", "id,name,status"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        # Check that fields are passed to render_table
        call_args = mock_render_table.call_args
        assert call_args[1]["fields"] == ["id", "name", "status"]

    @patch("taskdog.cli.commands.table.render_table")
    def test_with_date_range(self, mock_render_table):
        """Test table with date range options."""
        # Setup
        mock_result = MagicMock()
        self.api_client.list_tasks.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            table_command,
            ["--start-date", "2025-10-01", "--end-date", "2025-10-31"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.list_tasks.call_args[1]
        assert call_kwargs["start_date"] is not None
        assert call_kwargs["end_date"] is not None

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.list_tasks.side_effect = error

        # Execute
        result = self.runner.invoke(table_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("displaying tasks", error)
