"""Tests for update command."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.update import update_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestUpdateCommand:
    """Test cases for update command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_update_name(self):
        """Test updating task name."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        mock_result.updated_fields = {"name": "New name"}
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            update_command, ["1", "--name", "New name"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.update_task.call_args[1]
        assert call_kwargs["name"] == "New name"
        self.console_writer.task_fields_updated.assert_called_once()

    def test_update_name_empty_error(self):
        """Test error when name is empty."""
        result = self.runner.invoke(
            update_command, ["1", "--name", ""], obj=self.cli_context
        )

        assert result.exit_code != 0
        assert "cannot be empty or whitespace-only" in result.output
        self.api_client.update_task.assert_not_called()

    def test_update_name_whitespace_only_error(self):
        """Test error when name is whitespace-only."""
        result = self.runner.invoke(
            update_command, ["1", "--name", "   "], obj=self.cli_context
        )

        assert result.exit_code != 0
        assert "cannot be empty or whitespace-only" in result.output
        self.api_client.update_task.assert_not_called()

    def test_update_priority(self):
        """Test updating task priority."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        mock_result.updated_fields = {"priority": 5}
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            update_command, ["1", "--priority", "5"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.update_task.call_args[1]
        assert call_kwargs["priority"] == 5
        self.console_writer.task_fields_updated.assert_called_once()

    def test_update_status(self):
        """Test updating task status."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        mock_result.updated_fields = {"status": "IN_PROGRESS"}
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            update_command, ["1", "--status", "IN_PROGRESS"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.update_task.call_args[1]
        assert call_kwargs["status"] is not None

    def test_update_deadline(self):
        """Test updating task deadline."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        mock_result.updated_fields = {"deadline": "2025-12-31"}
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            update_command, ["1", "--deadline", "2025-12-31"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.update_task.call_args[1]
        assert call_kwargs["deadline"] is not None

    def test_update_multiple_fields(self):
        """Test updating multiple fields at once."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        mock_result.updated_fields = {"priority": 5, "deadline": "2025-12-31"}
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            update_command,
            ["1", "--priority", "5", "--deadline", "2025-12-31"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.update_task.call_args[1]
        assert call_kwargs["priority"] == 5
        assert call_kwargs["deadline"] is not None

    def test_update_planned_schedule(self):
        """Test updating planned start and end."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        mock_result.updated_fields = {
            "planned_start": "2025-10-15",
            "planned_end": "2025-10-17",
        }
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            update_command,
            ["1", "--planned-start", "2025-10-15", "--planned-end", "2025-10-17"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.update_task.call_args[1]
        assert call_kwargs["planned_start"] is not None
        assert call_kwargs["planned_end"] is not None

    def test_update_estimated_duration(self):
        """Test updating estimated duration."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        mock_result.updated_fields = {"estimated_duration": 4.0}
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(
            update_command, ["1", "--estimated-duration", "4.0"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        call_kwargs = self.api_client.update_task.call_args[1]
        assert call_kwargs["estimated_duration"] == 4.0

    def test_update_no_fields_warning(self):
        """Test warning when no fields are provided."""
        # Setup
        mock_task = MagicMock()
        mock_result = MagicMock()
        mock_result.task = mock_task
        mock_result.updated_fields = {}
        self.api_client.update_task.return_value = mock_result

        # Execute
        result = self.runner.invoke(update_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.warning.assert_called_once()

    def test_task_not_found(self):
        """Test update with non-existent task."""
        # Setup
        self.api_client.update_task.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(
            update_command, ["999", "--priority", "5"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_general_exception(self):
        """Test handling of general exception."""
        # Setup
        error = ValueError("Something went wrong")
        self.api_client.update_task.side_effect = error

        # Execute
        result = self.runner.invoke(
            update_command, ["1", "--priority", "5"], obj=self.cli_context
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once_with("updating task", error)

    def test_missing_task_id(self):
        """Test update without task_id argument."""
        result = self.runner.invoke(update_command, [], obj=self.cli_context)
        assert result.exit_code != 0
