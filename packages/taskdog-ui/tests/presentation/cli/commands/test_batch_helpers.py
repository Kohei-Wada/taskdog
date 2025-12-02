"""Tests for batch_helpers module."""

from unittest.mock import MagicMock, call

import pytest

from taskdog.cli.commands.batch_helpers import execute_batch_operation
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
)


class TestExecuteBatchOperation:
    """Test cases for execute_batch_operation function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.operation = MagicMock()
        self.operation_name = "test operation"

    def test_single_task_success(self):
        """Test successful operation on a single task."""
        task_ids = (1,)

        execute_batch_operation(
            task_ids, self.operation, self.console_writer, self.operation_name
        )

        # Verify operation was called once
        self.operation.assert_called_once_with(1)
        # Verify no spacing added for single task
        self.console_writer.empty_line.assert_not_called()
        # Verify no errors
        self.console_writer.validation_error.assert_not_called()
        self.console_writer.error.assert_not_called()

    def test_multiple_tasks_success(self):
        """Test successful operation on multiple tasks."""
        task_ids = (1, 2, 3)

        execute_batch_operation(
            task_ids, self.operation, self.console_writer, self.operation_name
        )

        # Verify operation was called for each task
        assert self.operation.call_count == 3
        self.operation.assert_has_calls([call(1), call(2), call(3)])
        # Verify spacing added after each task (3 tasks = 3 empty lines)
        assert self.console_writer.empty_line.call_count == 3

    def test_task_not_found_error(self):
        """Test handling of TaskNotFoundException."""
        task_ids = (1, 2)
        self.operation.side_effect = [
            TaskNotFoundException(1),
            None,  # Second task succeeds
        ]

        execute_batch_operation(
            task_ids, self.operation, self.console_writer, self.operation_name
        )

        # Verify operation was called for both tasks
        assert self.operation.call_count == 2
        # Verify error message was displayed
        error_msg = self.console_writer.validation_error.call_args[0][0]
        assert "Task with ID 1 not found" in error_msg
        # Verify spacing added after both tasks
        assert self.console_writer.empty_line.call_count == 2

    def test_task_already_finished_error(self):
        """Test handling of TaskAlreadyFinishedError."""
        task_ids = (1,)
        error = TaskAlreadyFinishedError(1, "COMPLETED")
        self.operation.side_effect = error

        execute_batch_operation(
            task_ids, self.operation, self.console_writer, self.operation_name
        )

        # Verify error message contains task ID and status
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        assert "task 1" in error_msg
        assert "COMPLETED" in error_msg
        assert self.operation_name in error_msg

    def test_task_not_started_error(self):
        """Test handling of TaskNotStartedError."""
        task_ids = (1,)
        error = TaskNotStartedError(1)
        self.operation.side_effect = error

        execute_batch_operation(
            task_ids, self.operation, self.console_writer, self.operation_name
        )

        # Verify error message contains task ID and suggestion
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        assert "task 1" in error_msg
        assert "PENDING" in error_msg
        assert "taskdog start 1" in error_msg

    def test_general_exception(self):
        """Test handling of general exceptions."""
        task_ids = (1,)
        error = ValueError("Something went wrong")
        self.operation.side_effect = error

        execute_batch_operation(
            task_ids, self.operation, self.console_writer, self.operation_name
        )

        # Verify error was passed to console_writer
        self.console_writer.error.assert_called_once_with(self.operation_name, error)

    def test_mixed_success_and_failure(self):
        """Test handling of mixed success and failure across multiple tasks."""
        task_ids = (1, 2, 3)
        self.operation.side_effect = [
            None,  # Task 1 succeeds
            TaskNotFoundException(2),  # Task 2 fails
            None,  # Task 3 succeeds
        ]

        execute_batch_operation(
            task_ids, self.operation, self.console_writer, self.operation_name
        )

        # Verify all tasks were attempted
        assert self.operation.call_count == 3
        # Verify one error was displayed
        error_msg = self.console_writer.validation_error.call_args[0][0]
        assert "Task with ID 2 not found" in error_msg
        # Verify spacing added after all tasks
        assert self.console_writer.empty_line.call_count == 3

    def test_empty_task_list(self):
        """Test handling of empty task list."""
        task_ids = ()

        execute_batch_operation(
            task_ids, self.operation, self.console_writer, self.operation_name
        )

        # Verify operation was never called
        self.operation.assert_not_called()
        # Verify no output
        self.console_writer.validation_error.assert_not_called()
        self.console_writer.error.assert_not_called()
        self.console_writer.empty_line.assert_not_called()

    def test_spacing_only_for_multiple_tasks(self):
        """Test that spacing is only added when processing multiple tasks."""
        # Single task - no spacing
        task_ids_single = (1,)
        execute_batch_operation(
            task_ids_single, self.operation, self.console_writer, self.operation_name
        )
        self.console_writer.empty_line.assert_not_called()

        # Reset mock
        self.console_writer.reset_mock()

        # Multiple tasks - spacing added
        task_ids_multiple = (1, 2)
        execute_batch_operation(
            task_ids_multiple, self.operation, self.console_writer, self.operation_name
        )
        assert self.console_writer.empty_line.call_count == 2
