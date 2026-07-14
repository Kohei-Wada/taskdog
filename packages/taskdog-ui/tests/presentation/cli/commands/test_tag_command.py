"""Tests for `tag` command group (list / set / rm)."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.tag.list import list_command
from taskdog.cli.commands.tag.remove import remove_command
from taskdog.cli.commands.tag.set import set_command
from taskdog_core.application.dto.delete_tag_output import DeleteTagOutput
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class _TagCommandFixture:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client


class TestTagListCommand(_TagCommandFixture):
    """Test cases for `tag list`."""

    def test_list_all_tags(self):
        """Test listing all tags without arguments."""
        mock_stats = MagicMock()
        mock_stats.tag_counts = {"work": 5, "urgent": 2, "personal": 3}
        self.api_client.get_tag_statistics.return_value = mock_stats

        result = self.runner.invoke(list_command, [], obj=self.cli_context)

        assert result.exit_code == 0
        self.api_client.get_tag_statistics.assert_called_once()
        self.console_writer.info.assert_called_once_with("All tags:")
        assert self.console_writer.print.call_count == 3

    def test_list_all_tags_empty(self):
        """Test listing all tags when no tags exist."""
        mock_stats = MagicMock()
        mock_stats.tag_counts = {}
        self.api_client.get_tag_statistics.return_value = mock_stats

        result = self.runner.invoke(list_command, [], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.info.assert_called_once_with("No tags found.")

    def test_show_task_tags(self):
        """Test showing tags for a specific task."""
        mock_task = MagicMock()
        mock_task.tags = ["work", "urgent"]
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.get_task_by_id.return_value = mock_result

        result = self.runner.invoke(list_command, ["5"], obj=self.cli_context)

        assert result.exit_code == 0
        self.api_client.get_task_by_id.assert_called_once_with(5)
        self.console_writer.info.assert_called_once_with("Tags for task 5:")
        assert self.console_writer.print.call_count == 2

    def test_show_task_tags_empty(self):
        """Test showing tags for a task with no tags."""
        mock_task = MagicMock()
        mock_task.tags = []
        mock_result = MagicMock()
        mock_result.task = mock_task
        self.api_client.get_task_by_id.return_value = mock_result

        result = self.runner.invoke(list_command, ["5"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.info.assert_called_once_with("Task 5 has no tags.")

    def test_show_task_tags_not_found(self):
        """Test showing tags for non-existent task."""
        self.api_client.get_task_by_id.side_effect = TaskNotFoundException(999)

        result = self.runner.invoke(list_command, ["999"], obj=self.cli_context)

        assert result.exit_code != 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        error = ValueError("Something went wrong")
        self.api_client.get_tag_statistics.side_effect = error

        result = self.runner.invoke(list_command, [], obj=self.cli_context)

        assert result.exit_code != 0
        self.console_writer.error.assert_called_once_with("listing tags", error)


class TestTagSetCommand(_TagCommandFixture):
    """Test cases for `tag set`."""

    def test_set_tags(self):
        """Test setting tags for a task."""
        mock_task = MagicMock()
        mock_task.tags = ["work", "urgent"]
        self.api_client.set_task_tags.return_value = mock_task

        result = self.runner.invoke(
            set_command, ["5", "work", "urgent"], obj=self.cli_context
        )

        assert result.exit_code == 0
        self.api_client.set_task_tags.assert_called_once_with(5, ["work", "urgent"])
        self.console_writer.task_success.assert_called_once_with(
            "Set tags for", mock_task
        )

    def test_clear_tags(self):
        """Test clearing tags for a task (no tags after operation)."""
        mock_task = MagicMock()
        mock_task.tags = []
        self.api_client.set_task_tags.return_value = mock_task

        result = self.runner.invoke(set_command, ["5"], obj=self.cli_context)

        assert result.exit_code == 0
        self.api_client.set_task_tags.assert_called_once_with(5, [])
        self.console_writer.task_success.assert_called_once_with(
            "Cleared tags for", mock_task
        )

    def test_task_not_found_on_set(self):
        """Test setting tags for non-existent task."""
        self.api_client.set_task_tags.side_effect = TaskNotFoundException(999)

        result = self.runner.invoke(set_command, ["999", "work"], obj=self.cli_context)

        assert result.exit_code != 0
        self.console_writer.validation_error.assert_called_once()


class TestTagRemoveCommand(_TagCommandFixture):
    """Test cases for `tag rm`."""

    def test_delete_tag_success(self):
        """Test deleting a tag successfully."""
        self.api_client.delete_tag.return_value = DeleteTagOutput(
            tag_name="urgent", affected_task_count=3
        )

        result = self.runner.invoke(remove_command, ["urgent"], obj=self.cli_context)

        assert result.exit_code == 0
        self.api_client.delete_tag.assert_called_once_with("urgent")
        self.console_writer.success.assert_called_once_with(
            "Deleted tag: urgent (removed from 3 tasks)"
        )

    def test_delete_tag_single_task(self):
        """Test deleting a tag from a single task uses singular 'task'."""
        self.api_client.delete_tag.return_value = DeleteTagOutput(
            tag_name="unique", affected_task_count=1
        )

        result = self.runner.invoke(remove_command, ["unique"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.success.assert_called_once_with(
            "Deleted tag: unique (removed from 1 task)"
        )

    def test_delete_tag_zero_tasks(self):
        """Test deleting a tag with no task associations."""
        self.api_client.delete_tag.return_value = DeleteTagOutput(
            tag_name="orphan", affected_task_count=0
        )

        result = self.runner.invoke(remove_command, ["orphan"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.success.assert_called_once_with(
            "Deleted tag: orphan (removed from 0 tasks)"
        )

    def test_delete_tag_not_found(self):
        """Test deleting a non-existent tag shows error."""
        self.api_client.delete_tag.side_effect = TaskNotFoundException(
            "Tag 'nonexistent' not found"
        )

        result = self.runner.invoke(
            remove_command, ["nonexistent"], obj=self.cli_context
        )

        assert result.exit_code != 0
        self.console_writer.validation_error.assert_called_once()

    def test_delete_tag_general_exception(self):
        """Test handling of general exception during tag deletion."""
        error = ValueError("Something went wrong")
        self.api_client.delete_tag.side_effect = error

        result = self.runner.invoke(remove_command, ["test"], obj=self.cli_context)

        assert result.exit_code != 0
        self.console_writer.error.assert_called_once_with("deleting tag", error)
