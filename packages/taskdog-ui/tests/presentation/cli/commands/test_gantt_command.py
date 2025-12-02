"""Tests for gantt command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.gantt import gantt_command


class TestGanttCommand:
    """Test cases for gantt command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.gantt.RichGanttRenderer")
    @patch("taskdog.cli.commands.gantt.GanttPresenter")
    def test_basic_display(self, mock_presenter_class, mock_renderer_class):
        """Test basic gantt display."""
        # Setup
        mock_gantt_result = MagicMock()
        self.api_client.get_gantt_data.return_value = mock_gantt_result

        mock_presenter = MagicMock()
        mock_presenter_class.return_value = mock_presenter
        mock_view_model = MagicMock()
        mock_presenter.present.return_value = mock_view_model

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Execute
        result = self.runner.invoke(gantt_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.get_gantt_data.assert_called_once()
        mock_presenter.present.assert_called_once_with(mock_gantt_result)
        mock_renderer.render.assert_called_once_with(mock_view_model)

    @patch("taskdog.cli.commands.gantt.RichGanttRenderer")
    @patch("taskdog.cli.commands.gantt.GanttPresenter")
    def test_with_all_option(self, mock_presenter_class, mock_renderer_class):
        """Test gantt with --all option."""
        # Setup
        mock_gantt_result = MagicMock()
        self.api_client.get_gantt_data.return_value = mock_gantt_result
        mock_presenter_class.return_value.present.return_value = MagicMock()

        # Execute
        result = self.runner.invoke(gantt_command, ["--all"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.get_gantt_data.call_args[1]
        assert call_kwargs["all"] is True

    @patch("taskdog.cli.commands.gantt.RichGanttRenderer")
    @patch("taskdog.cli.commands.gantt.GanttPresenter")
    def test_with_status_filter(self, mock_presenter_class, mock_renderer_class):
        """Test gantt with --status filter."""
        # Setup
        mock_gantt_result = MagicMock()
        self.api_client.get_gantt_data.return_value = mock_gantt_result
        mock_presenter_class.return_value.present.return_value = MagicMock()

        # Execute
        result = self.runner.invoke(
            gantt_command, ["--status", "completed"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.get_gantt_data.call_args[1]
        assert call_kwargs["status"] == "completed"

    @patch("taskdog.cli.commands.gantt.RichGanttRenderer")
    @patch("taskdog.cli.commands.gantt.GanttPresenter")
    def test_with_tags_filter(self, mock_presenter_class, mock_renderer_class):
        """Test gantt with --tag filter."""
        # Setup
        mock_gantt_result = MagicMock()
        self.api_client.get_gantt_data.return_value = mock_gantt_result
        mock_presenter_class.return_value.present.return_value = MagicMock()

        # Execute
        result = self.runner.invoke(
            gantt_command, ["-t", "work", "-t", "urgent"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.get_gantt_data.call_args[1]
        assert call_kwargs["tags"] == ["work", "urgent"]

    @patch("taskdog.cli.commands.gantt.RichGanttRenderer")
    @patch("taskdog.cli.commands.gantt.GanttPresenter")
    def test_with_sort_option(self, mock_presenter_class, mock_renderer_class):
        """Test gantt with --sort and --reverse options."""
        # Setup
        mock_gantt_result = MagicMock()
        self.api_client.get_gantt_data.return_value = mock_gantt_result
        mock_presenter_class.return_value.present.return_value = MagicMock()

        # Execute
        result = self.runner.invoke(
            gantt_command, ["--sort", "priority", "--reverse"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.get_gantt_data.call_args[1]
        assert call_kwargs["sort_by"] == "priority"
        assert call_kwargs["reverse"] is True

    @patch("taskdog.cli.commands.gantt.RichGanttRenderer")
    @patch("taskdog.cli.commands.gantt.GanttPresenter")
    def test_with_date_range(self, mock_presenter_class, mock_renderer_class):
        """Test gantt with date range options."""
        # Setup
        mock_gantt_result = MagicMock()
        self.api_client.get_gantt_data.return_value = mock_gantt_result
        mock_presenter_class.return_value.present.return_value = MagicMock()

        # Execute
        result = self.runner.invoke(
            gantt_command,
            ["--start-date", "2025-10-01", "--end-date", "2025-10-31"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.get_gantt_data.call_args[1]
        assert call_kwargs["start_date"] is not None
        assert call_kwargs["end_date"] is not None

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.get_gantt_data.side_effect = error

        # Execute
        result = self.runner.invoke(gantt_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with(
            "displaying Gantt chart", error
        )
