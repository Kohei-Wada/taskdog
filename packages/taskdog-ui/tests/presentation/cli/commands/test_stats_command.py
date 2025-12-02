"""Tests for stats command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.stats import stats_command


class TestStatsCommand:
    """Test cases for stats command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.stats.RichStatisticsRenderer")
    @patch("taskdog.cli.commands.stats.StatisticsMapper")
    def test_basic_display(self, mock_mapper_class, mock_renderer_class):
        """Test basic stats display."""
        # Setup
        mock_result = MagicMock()
        mock_result.task_stats.total_tasks = 10
        self.api_client.calculate_statistics.return_value = mock_result

        mock_view_model = MagicMock()
        mock_mapper_class.from_statistics_result.return_value = mock_view_model

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Execute
        result = self.runner.invoke(stats_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.calculate_statistics.assert_called_once_with(period="all")
        mock_mapper_class.from_statistics_result.assert_called_once_with(mock_result)
        mock_renderer.render.assert_called_once_with(mock_view_model, focus="all")

    @patch("taskdog.cli.commands.stats.RichStatisticsRenderer")
    @patch("taskdog.cli.commands.stats.StatisticsMapper")
    def test_with_period_option(self, mock_mapper_class, mock_renderer_class):
        """Test stats with --period option."""
        # Setup
        mock_result = MagicMock()
        mock_result.task_stats.total_tasks = 10
        self.api_client.calculate_statistics.return_value = mock_result
        mock_mapper_class.from_statistics_result.return_value = MagicMock()

        # Execute
        result = self.runner.invoke(
            stats_command, ["--period", "7d"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.calculate_statistics.assert_called_once_with(period="7d")

    @patch("taskdog.cli.commands.stats.RichStatisticsRenderer")
    @patch("taskdog.cli.commands.stats.StatisticsMapper")
    def test_with_focus_option(self, mock_mapper_class, mock_renderer_class):
        """Test stats with --focus option."""
        # Setup
        mock_result = MagicMock()
        mock_result.task_stats.total_tasks = 10
        self.api_client.calculate_statistics.return_value = mock_result
        mock_mapper_class.from_statistics_result.return_value = MagicMock()

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Execute
        result = self.runner.invoke(
            stats_command, ["--focus", "time"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        mock_renderer.render.assert_called_once()
        call_kwargs = mock_renderer.render.call_args[1]
        assert call_kwargs["focus"] == "time"

    def test_no_tasks_warning(self):
        """Test stats when no tasks found."""
        # Setup
        mock_result = MagicMock()
        mock_result.task_stats.total_tasks = 0
        self.api_client.calculate_statistics.return_value = mock_result

        # Execute
        result = self.runner.invoke(stats_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.warning.assert_called_once_with(
            "No tasks found to analyze."
        )

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.calculate_statistics.side_effect = error

        # Execute
        result = self.runner.invoke(stats_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with(
            "calculating statistics", error
        )

    @patch("taskdog.cli.commands.stats.RichStatisticsRenderer")
    @patch("taskdog.cli.commands.stats.StatisticsMapper")
    def test_period_30d(self, mock_mapper_class, mock_renderer_class):
        """Test stats with 30d period."""
        # Setup
        mock_result = MagicMock()
        mock_result.task_stats.total_tasks = 10
        self.api_client.calculate_statistics.return_value = mock_result
        mock_mapper_class.from_statistics_result.return_value = MagicMock()

        # Execute
        result = self.runner.invoke(
            stats_command, ["--period", "30d"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.calculate_statistics.assert_called_once_with(period="30d")

    @pytest.mark.parametrize(
        "focus",
        ["basic", "time", "estimation", "deadline", "priority", "trends"],
        ids=["basic", "time", "estimation", "deadline", "priority", "trends"],
    )
    @patch("taskdog.cli.commands.stats.RichStatisticsRenderer")
    @patch("taskdog.cli.commands.stats.StatisticsMapper")
    def test_focus_options(self, mock_mapper_class, mock_renderer_class, focus):
        """Test different focus options."""
        # Setup
        mock_result = MagicMock()
        mock_result.task_stats.total_tasks = 10
        self.api_client.calculate_statistics.return_value = mock_result
        mock_mapper_class.from_statistics_result.return_value = MagicMock()

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Execute
        result = self.runner.invoke(
            stats_command, ["--focus", focus], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
