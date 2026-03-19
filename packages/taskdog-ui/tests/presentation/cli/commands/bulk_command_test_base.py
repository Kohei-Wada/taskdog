"""Base test class for CLI bulk command tests."""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog_core.application.dto.bulk_operation_output import (
    BulkOperationOutput,
    BulkTaskResultOutput,
)
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import TaskStatus


def make_success_result(
    task_id: int, name: str = "Test Task", status: TaskStatus = TaskStatus.COMPLETED
) -> BulkTaskResultOutput:
    """Create a successful bulk result."""
    task = TaskOperationOutput(
        id=task_id,
        name=name,
        status=status,
        priority=5,
        deadline=None,
        estimated_duration=None,
        planned_start=None,
        planned_end=None,
        actual_start=None,
        actual_end=None,
        actual_duration=None,
        depends_on=[],
        tags=[],
        is_fixed=False,
        is_archived=False,
        actual_duration_hours=None,
        daily_allocations={},
    )
    return BulkTaskResultOutput(
        task_id=task_id,
        success=True,
        task=task,
        error=None,
    )


def make_failure_result(task_id: int, error: str) -> BulkTaskResultOutput:
    """Create a failed bulk result."""
    return BulkTaskResultOutput(
        task_id=task_id,
        success=False,
        task=None,
        error=error,
    )


class BaseBulkCommandTest:
    """Base test class for CLI commands that use bulk API.

    Subclasses must override:
    - command_func: The Click command function to test
    - bulk_method: Name of the bulk API method (e.g., "bulk_start")
    - action_verb: Past tense action verb (e.g., "Started")
    """

    command_func = None
    bulk_method: str | None = None
    action_verb: str | None = None

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up common test fixtures."""
        if self.__class__ is BaseBulkCommandTest:
            pytest.skip("Skipping base test class")

        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def _set_bulk_return(self, results: list[BulkTaskResultOutput]) -> None:
        """Set the return value for the bulk API method."""
        getattr(self.api_client, self.bulk_method).return_value = BulkOperationOutput(
            results=results
        )

    def test_single_task_success(self):
        """Test executing command on a single task successfully."""
        result_item = make_success_result(1)
        self._set_bulk_return([result_item])

        result = self.runner.invoke(self.command_func, ["1"], obj=self.cli_context)

        assert result.exit_code == 0
        getattr(self.api_client, self.bulk_method).assert_called_once_with([1])
        self.console_writer.task_success.assert_called_once_with(
            self.action_verb, result_item.task
        )

    def test_multiple_tasks_success(self):
        """Test executing command on multiple tasks successfully."""
        self._set_bulk_return(
            [
                make_success_result(1, "Task 1"),
                make_success_result(2, "Task 2"),
            ]
        )

        result = self.runner.invoke(self.command_func, ["1", "2"], obj=self.cli_context)

        assert result.exit_code == 0
        getattr(self.api_client, self.bulk_method).assert_called_once_with([1, 2])
        assert self.console_writer.task_success.call_count == 2
        assert self.console_writer.empty_line.call_count == 2

    def test_nonexistent_task(self):
        """Test command with non-existent task."""
        self._set_bulk_return(
            [
                make_failure_result(999, "Task with ID 999 not found"),
            ]
        )

        result = self.runner.invoke(self.command_func, ["999"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once_with(
            "Task with ID 999 not found"
        )

    def test_mixed_success_and_failure(self):
        """Test command with mixed success and failure."""
        self._set_bulk_return(
            [
                make_success_result(1),
                make_failure_result(999, "Task with ID 999 not found"),
            ]
        )

        result = self.runner.invoke(
            self.command_func, ["1", "999"], obj=self.cli_context
        )

        assert result.exit_code == 0
        self.console_writer.task_success.assert_called_once()
        self.console_writer.validation_error.assert_called_once()
        assert self.console_writer.empty_line.call_count == 2

    def test_no_task_id_provided(self):
        """Test command without providing task ID."""
        result = self.runner.invoke(self.command_func, [], obj=self.cli_context)
        assert result.exit_code != 0
