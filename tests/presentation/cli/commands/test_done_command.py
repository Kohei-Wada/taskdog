"""Tests for done command."""

import unittest
from unittest.mock import patch

from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
)
from presentation.cli.commands.done import done_command
from tests.presentation.cli.commands.base_command_test import BaseBatchCommandTest


class TestDoneCommand(BaseBatchCommandTest):
    """Test cases for done command."""

    @patch("presentation.cli.commands.done.CompleteTaskUseCase")
    def test_complete_single_task_success(self, mock_use_case_class):
        """Test completing a single task successfully."""
        # Setup
        completed_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.COMPLETED)

        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.return_value = completed_task

        # Execute
        result = self.runner.invoke(done_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        mock_use_case.execute.assert_called_once()
        self.console_writer.task_success.assert_called_once_with("Completed", completed_task)
        self.console_writer.task_completion_details.assert_called_once_with(completed_task)

    @patch("presentation.cli.commands.done.CompleteTaskUseCase")
    def test_complete_multiple_tasks_success(self, mock_use_case_class):
        """Test completing multiple tasks successfully."""
        # Setup
        completed_tasks = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.COMPLETED),
            Task(id=2, name="Task 2", priority=5, status=TaskStatus.COMPLETED),
        ]

        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = completed_tasks

        # Execute
        result = self.runner.invoke(done_command, ["1", "2"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_use_case.execute.call_count, 2)
        self.assertEqual(self.console_writer.task_success.call_count, 2)
        self.assertEqual(self.console_writer.task_completion_details.call_count, 2)
        # Verify spacing added for multiple tasks
        self.assertEqual(self.console_writer.empty_line.call_count, 2)

    @patch("presentation.cli.commands.done.CompleteTaskUseCase")
    def test_complete_nonexistent_task(self, mock_use_case_class):
        """Test completing a task that doesn't exist."""
        # Setup
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(done_command, ["999"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("999", error_msg)

    @patch("presentation.cli.commands.done.CompleteTaskUseCase")
    def test_complete_already_finished_task(self, mock_use_case_class):
        """Test completing a task that is already finished."""
        # Setup
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskAlreadyFinishedError(1, "COMPLETED")

        # Execute
        result = self.runner.invoke(done_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("task 1", error_msg)
        self.assertIn("COMPLETED", error_msg)

    @patch("presentation.cli.commands.done.CompleteTaskUseCase")
    def test_complete_not_started_task(self, mock_use_case_class):
        """Test completing a task that hasn't been started."""
        # Setup
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskNotStartedError(1)

        # Execute
        result = self.runner.invoke(done_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("task 1", error_msg)
        self.assertIn("PENDING", error_msg)
        self.assertIn("taskdog start 1", error_msg)

    @patch("presentation.cli.commands.done.CompleteTaskUseCase")
    def test_complete_general_exception(self, mock_use_case_class):
        """Test handling of general exception during completion."""
        # Setup
        mock_use_case = mock_use_case_class.return_value
        error = ValueError("Something went wrong")
        mock_use_case.execute.side_effect = error

        # Execute
        result = self.runner.invoke(done_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("complete", error)

    def test_complete_no_task_id_provided(self):
        """Test done command without providing task ID."""
        # Execute
        result = self.runner.invoke(done_command, [], obj=self.cli_context)

        # Verify - Click handles missing required argument
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
