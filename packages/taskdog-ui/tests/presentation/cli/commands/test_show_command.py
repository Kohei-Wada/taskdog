"""Tests for show command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.show import show_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestShowCommand:
    """Test cases for show command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.show.RichDetailRenderer")
    def test_basic_show(self, mock_renderer_class):
        """Test basic show display."""
        # Setup
        mock_detail = MagicMock()
        self.api_client.get_task_detail.return_value = mock_detail

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Execute
        result = self.runner.invoke(show_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.get_task_detail.assert_called_once_with(1)
        mock_renderer.render.assert_called_once_with(mock_detail, raw=False)

    @patch("taskdog.cli.commands.show.RichDetailRenderer")
    def test_with_raw_option(self, mock_renderer_class):
        """Test show with --raw option."""
        # Setup
        mock_detail = MagicMock()
        self.api_client.get_task_detail.return_value = mock_detail

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Execute
        result = self.runner.invoke(show_command, ["1", "--raw"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        mock_renderer.render.assert_called_once_with(mock_detail, raw=True)

    def test_task_not_found(self):
        """Test show with non-existent task."""
        # Setup
        self.api_client.get_task_detail.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(show_command, ["999"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.get_task_detail.side_effect = error

        # Execute
        result = self.runner.invoke(show_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("showing task", error)

    def test_missing_task_id(self):
        """Test show without task_id argument."""
        result = self.runner.invoke(show_command, [], obj=self.cli_context)
        assert result.exit_code != 0
