"""Tests for tag command (tag management)."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.tag import tag_command
from taskdog_core.application.dto.delete_tag_output import DeleteTagOutput
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestTagCommand:
    """Test cases for tag command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_delete_tag_success(self):
        """Test deleting a tag successfully."""
        # Setup
        self.api_client.delete_tag.return_value = DeleteTagOutput(
            tag_name="urgent", affected_task_count=3
        )

        # Execute
        result = self.runner.invoke(tag_command, ["-d", "urgent"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.delete_tag.assert_called_once_with("urgent")
        self.console_writer.success.assert_called_once_with(
            "Deleted tag: urgent (removed from 3 tasks)"
        )

    def test_delete_tag_single_task(self):
        """Test deleting a tag from a single task uses singular 'task'."""
        # Setup
        self.api_client.delete_tag.return_value = DeleteTagOutput(
            tag_name="unique", affected_task_count=1
        )

        # Execute
        result = self.runner.invoke(tag_command, ["-d", "unique"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.success.assert_called_once_with(
            "Deleted tag: unique (removed from 1 task)"
        )

    def test_delete_tag_zero_tasks(self):
        """Test deleting a tag with no task associations."""
        # Setup
        self.api_client.delete_tag.return_value = DeleteTagOutput(
            tag_name="orphan", affected_task_count=0
        )

        # Execute
        result = self.runner.invoke(tag_command, ["-d", "orphan"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.success.assert_called_once_with(
            "Deleted tag: orphan (removed from 0 tasks)"
        )

    def test_delete_tag_not_found(self):
        """Test deleting a non-existent tag shows error."""
        # Setup
        self.api_client.delete_tag.side_effect = TaskNotFoundException(
            "Tag 'nonexistent' not found"
        )

        # Execute
        result = self.runner.invoke(
            tag_command, ["-d", "nonexistent"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_no_option_shows_usage(self):
        """Test running without options shows usage info."""
        # Execute
        result = self.runner.invoke(tag_command, [], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.info.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.delete_tag.side_effect = error

        # Execute
        result = self.runner.invoke(tag_command, ["-d", "test"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("managing tag", error)
