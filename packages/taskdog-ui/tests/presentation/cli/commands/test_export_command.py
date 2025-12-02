"""Tests for export command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.export import export_command


class TestExportCommand:
    """Test cases for export command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    @patch("taskdog.cli.commands.export.JsonTaskExporter")
    def test_basic_export_json(self, mock_exporter_class):
        """Test basic JSON export to stdout."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = [MagicMock()]
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = '{"tasks": []}'
        mock_exporter_class.return_value = mock_exporter

        # Execute
        result = self.runner.invoke(export_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.list_tasks.assert_called_once()
        mock_exporter.export.assert_called_once()

    @patch("taskdog.cli.commands.export.CsvTaskExporter")
    def test_export_csv(self, mock_exporter_class):
        """Test CSV export."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = [MagicMock()]
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = "id,name\n1,Task"
        mock_exporter_class.return_value = mock_exporter

        # Execute
        result = self.runner.invoke(
            export_command, ["--format", "csv"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        mock_exporter_class.assert_called_once()

    @patch("taskdog.cli.commands.export.MarkdownTableExporter")
    def test_export_markdown(self, mock_exporter_class):
        """Test Markdown export."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = [MagicMock()]
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = "| id | name |\n|---|---|"
        mock_exporter_class.return_value = mock_exporter

        # Execute
        result = self.runner.invoke(
            export_command, ["--format", "markdown"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        mock_exporter_class.assert_called_once()

    @patch("taskdog.cli.commands.export.JsonTaskExporter")
    def test_export_to_file(self, mock_exporter_class):
        """Test export to file."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = [MagicMock()]
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = '{"tasks": []}'
        mock_exporter_class.return_value = mock_exporter

        # Execute with isolated filesystem
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                export_command, ["-o", "tasks.json"], obj=self.cli_context
            )

            # Verify
            assert result.exit_code == 0
            self.console_writer.success.assert_called_once()

    @patch("taskdog.cli.commands.export.JsonTaskExporter")
    def test_export_with_all_option(self, mock_exporter_class):
        """Test export with --all option."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = []
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = '{"tasks": []}'
        mock_exporter_class.return_value = mock_exporter

        # Execute
        result = self.runner.invoke(export_command, ["--all"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.list_tasks.call_args[1]
        assert call_kwargs["all"] is True

    @patch("taskdog.cli.commands.export.JsonTaskExporter")
    def test_export_with_status_filter(self, mock_exporter_class):
        """Test export with --status filter."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = []
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = '{"tasks": []}'
        mock_exporter_class.return_value = mock_exporter

        # Execute
        result = self.runner.invoke(
            export_command, ["--status", "completed"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.list_tasks.call_args[1]
        assert call_kwargs["status"] == "completed"

    @patch("taskdog.cli.commands.export.JsonTaskExporter")
    def test_export_with_tags_filter(self, mock_exporter_class):
        """Test export with --tag filter."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = []
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = '{"tasks": []}'
        mock_exporter_class.return_value = mock_exporter

        # Execute
        result = self.runner.invoke(
            export_command, ["-t", "work", "-t", "urgent"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.list_tasks.call_args[1]
        assert call_kwargs["tags"] == ["work", "urgent"]

    @patch("taskdog.cli.commands.export.JsonTaskExporter")
    def test_export_with_fields(self, mock_exporter_class):
        """Test export with --fields option."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = []
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = '{"tasks": []}'
        mock_exporter_class.return_value = mock_exporter

        # Execute
        result = self.runner.invoke(
            export_command, ["--fields", "id,name,status"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        mock_exporter_class.assert_called_once_with(field_list=["id", "name", "status"])

    @patch("taskdog.cli.commands.export.JsonTaskExporter")
    def test_export_with_date_range(self, mock_exporter_class):
        """Test export with date range options."""
        # Setup
        mock_result = MagicMock()
        mock_result.tasks = []
        self.api_client.list_tasks.return_value = mock_result

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = '{"tasks": []}'
        mock_exporter_class.return_value = mock_exporter

        # Execute
        result = self.runner.invoke(
            export_command,
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
        result = self.runner.invoke(export_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code != 0  # Raises Abort
        self.console_writer.error.assert_called_once()
