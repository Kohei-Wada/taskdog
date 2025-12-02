"""Tests for tags command."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.tags import tags_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestTagsCommand:
    """Test cases for tags command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_list_all_tags(self):
        """Test listing all tags without arguments."""
        # Setup
        mock_stats = MagicMock()
        mock_stats.tag_counts = {"work": 5, "urgent": 2, "personal": 3}
        self.api_client.get_tag_statistics.return_value = mock_stats

        # Execute
        result = self.runner.invoke(tags_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.get_tag_statistics.assert_called_once()
        self.console_writer.info.assert_called_once_with("All tags:")
        # 3 tags should be printed
        assert self.console_writer.print.call_count == 3

    def test_list_all_tags_empty(self):
        """Test listing all tags when no tags exist."""
        # Setup
        mock_stats = MagicMock()
        mock_stats.tag_counts = {}
        self.api_client.get_tag_statistics.return_value = mock_stats

        # Execute
        result = self.runner.invoke(tags_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.info.assert_called_once_with("No tags found.")

    def test_show_task_tags(self):
        """Test showing tags for a specific task."""
        # Setup
        mock_task = MagicMock()
        mock_task.tags = ["work", "urgent"]
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.get_task_by_id.return_value = mock_result

        # Execute
        result = self.runner.invoke(tags_command, ["5"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.get_task_by_id.assert_called_once_with(5)
        self.console_writer.info.assert_called_once_with("Tags for task 5:")
        assert self.console_writer.print.call_count == 2

    def test_show_task_tags_empty(self):
        """Test showing tags for a task with no tags."""
        # Setup
        mock_task = MagicMock()
        mock_task.tags = []
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.get_task_by_id.return_value = mock_result

        # Execute
        result = self.runner.invoke(tags_command, ["5"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.info.assert_called_once_with("Task 5 has no tags.")

    def test_show_task_tags_not_found(self):
        """Test showing tags for non-existent task."""
        # Setup
        mock_result = MagicMock()
        mock_result.task = None
        self.api_client.get_task_by_id.return_value = mock_result

        # Execute
        result = self.runner.invoke(tags_command, ["999"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_set_tags(self):
        """Test setting tags for a task."""
        # Setup
        mock_task = MagicMock()
        mock_task.tags = ["work", "urgent"]
        self.api_client.set_task_tags.return_value = mock_task

        # Execute
        result = self.runner.invoke(
            tags_command, ["5", "work", "urgent"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.set_task_tags.assert_called_once_with(5, ["work", "urgent"])
        self.console_writer.task_success.assert_called_once_with(
            "Set tags for", mock_task
        )

    def test_clear_tags(self):
        """Test clearing tags for a task (empty tags list)."""
        # Setup
        mock_task = MagicMock()
        mock_task.tags = []
        self.api_client.set_task_tags.return_value = mock_task

        # Execute - set with empty result
        result = self.runner.invoke(
            tags_command, ["5", "cleared"], obj=self.cli_context
        )

        # Verify - mock simulates the task having no tags after operation
        assert result.exit_code == 0
        self.console_writer.task_success.assert_called_once_with(
            "Cleared tags for", mock_task
        )

    def test_task_not_found_on_set(self):
        """Test setting tags for non-existent task."""
        # Setup
        self.api_client.set_task_tags.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(tags_command, ["999", "work"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.get_tag_statistics.side_effect = error

        # Execute
        result = self.runner.invoke(tags_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("managing tags", error)
