"""Tests for rm command."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.rm import rm_command
from taskdog_core.application.dto.bulk_operation_output import (
    BulkOperationOutput,
    BulkTaskResultOutput,
)
from tests.presentation.cli.commands.bulk_command_test_base import (
    make_failure_result,
    make_success_result,
)


class TestRmCommand:
    """Test cases for rm command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def _set_archive_return(self, results):
        self.api_client.bulk_archive.return_value = BulkOperationOutput(results=results)

    def _set_delete_return(self, results):
        self.api_client.bulk_delete.return_value = BulkOperationOutput(results=results)

    def test_single_task_archive_default(self):
        """Test archiving a single task (default behavior)."""
        result_item = make_success_result(1)
        self._set_archive_return([result_item])

        result = self.runner.invoke(rm_command, ["1"], obj=self.cli_context)

        assert result.exit_code == 0
        self.api_client.bulk_archive.assert_called_once_with([1])
        self.api_client.bulk_delete.assert_not_called()
        self.console_writer.task_success.assert_called_once()
        self.console_writer.info.assert_called_once()

    def test_single_task_hard_delete(self):
        """Test hard deleting a single task."""
        delete_result = BulkTaskResultOutput(
            task_id=1, success=True, task=None, error=None
        )
        self._set_delete_return([delete_result])

        result = self.runner.invoke(rm_command, ["1", "--hard"], obj=self.cli_context)

        assert result.exit_code == 0
        self.api_client.bulk_delete.assert_called_once_with([1])
        self.api_client.bulk_archive.assert_not_called()
        self.console_writer.success.assert_called_once()
        assert "Permanently deleted" in self.console_writer.success.call_args[0][0]

    def test_multiple_tasks_archive(self):
        """Test archiving multiple tasks."""
        self._set_archive_return(
            [
                make_success_result(1, "Task 1"),
                make_success_result(2, "Task 2"),
            ]
        )

        result = self.runner.invoke(rm_command, ["1", "2"], obj=self.cli_context)

        assert result.exit_code == 0
        self.api_client.bulk_archive.assert_called_once_with([1, 2])
        assert self.console_writer.task_success.call_count == 2
        assert self.console_writer.empty_line.call_count == 2

    def test_multiple_tasks_hard_delete(self):
        """Test hard deleting multiple tasks."""
        self._set_delete_return(
            [
                BulkTaskResultOutput(task_id=1, success=True, task=None, error=None),
                BulkTaskResultOutput(task_id=2, success=True, task=None, error=None),
            ]
        )

        result = self.runner.invoke(
            rm_command, ["1", "2", "--hard"], obj=self.cli_context
        )

        assert result.exit_code == 0
        self.api_client.bulk_delete.assert_called_once_with([1, 2])
        assert self.console_writer.success.call_count == 2

    def test_task_not_found_archive(self):
        """Test archive with non-existent task."""
        self._set_archive_return(
            [
                make_failure_result(999, "Task with ID 999 not found"),
            ]
        )

        result = self.runner.invoke(rm_command, ["999"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_task_not_found_hard_delete(self):
        """Test hard delete with non-existent task."""
        self._set_delete_return(
            [
                make_failure_result(999, "Task with ID 999 not found"),
            ]
        )

        result = self.runner.invoke(rm_command, ["999", "--hard"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_archive_restore_hint(self):
        """Test archive shows restore hint."""
        result_item = make_success_result(5)
        self._set_archive_return([result_item])

        result = self.runner.invoke(rm_command, ["5"], obj=self.cli_context)

        assert result.exit_code == 0
        info_msg = self.console_writer.info.call_args[0][0]
        assert "taskdog restore 5" in info_msg

    def test_no_task_id_provided(self):
        """Test rm without providing task ID."""
        result = self.runner.invoke(rm_command, [], obj=self.cli_context)
        assert result.exit_code != 0
