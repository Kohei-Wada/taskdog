"""Tests for start command."""

import unittest
from unittest.mock import patch

from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskAlreadyFinishedError, TaskNotFoundException
from presentation.cli.commands.start import start_command
from tests.presentation.cli.commands.base_command_test import BaseBatchCommandTest


class TestStartCommand(BaseBatchCommandTest):
    """Test cases for start command."""

    @patch("presentation.cli.commands.start.StartTaskUseCase")
    def test_start_single_task_success(self, mock_use_case_class):
        """Test starting a single task successfully."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.PENDING)
        updated_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.IN_PROGRESS)

        self.repository.get_by_id.return_value = task
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.return_value = updated_task

        # Execute
        result = self.runner.invoke(start_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        mock_use_case.execute.assert_called_once()
        self.console_writer.task_success.assert_called_once_with("Started", updated_task)
        self.console_writer.task_start_time.assert_called_once()

    @patch("presentation.cli.commands.start.StartTaskUseCase")
    def test_start_multiple_tasks_success(self, mock_use_case_class):
        """Test starting multiple tasks successfully."""
        # Setup
        tasks = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.PENDING),
            Task(id=2, name="Task 2", priority=5, status=TaskStatus.PENDING),
        ]
        updated_tasks = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.IN_PROGRESS),
            Task(id=2, name="Task 2", priority=5, status=TaskStatus.IN_PROGRESS),
        ]

        self.repository.get_by_id.side_effect = tasks
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = updated_tasks

        # Execute
        result = self.runner.invoke(start_command, ["1", "2"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_use_case.execute.call_count, 2)
        self.assertEqual(self.console_writer.task_success.call_count, 2)
        # Verify spacing added for multiple tasks
        self.assertEqual(self.console_writer.empty_line.call_count, 2)

    @patch("presentation.cli.commands.start.StartTaskUseCase")
    def test_start_already_in_progress_task(self, mock_use_case_class):
        """Test starting a task that is already in progress."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.IN_PROGRESS)

        self.repository.get_by_id.return_value = task
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.return_value = task

        # Execute
        result = self.runner.invoke(start_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        # Should still show success message
        self.console_writer.task_success.assert_called_once()
        # Should indicate task was already in progress
        call_args = self.console_writer.task_start_time.call_args
        self.assertTrue(call_args[0][1])  # was_already_in_progress = True

    @patch("presentation.cli.commands.start.StartTaskUseCase")
    def test_start_nonexistent_task(self, mock_use_case_class):
        """Test starting a task that doesn't exist."""
        # Setup
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(start_command, ["999"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)  # Command doesn't fail, just shows error
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("999", error_msg)

    @patch("presentation.cli.commands.start.StartTaskUseCase")
    def test_start_already_finished_task(self, mock_use_case_class):
        """Test starting a task that is already finished."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.COMPLETED)
        self.repository.get_by_id.return_value = task

        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskAlreadyFinishedError(1, "COMPLETED")

        # Execute
        result = self.runner.invoke(start_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("task 1", error_msg)
        self.assertIn("COMPLETED", error_msg)

    @patch("presentation.cli.commands.start.StartTaskUseCase")
    def test_start_general_exception(self, mock_use_case_class):
        """Test handling of general exception during start."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.PENDING)
        self.repository.get_by_id.return_value = task

        mock_use_case = mock_use_case_class.return_value
        error = ValueError("Something went wrong")
        mock_use_case.execute.side_effect = error

        # Execute
        result = self.runner.invoke(start_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("start", error)

    def test_start_no_task_id_provided(self):
        """Test start command without providing task ID."""
        # Execute
        result = self.runner.invoke(start_command, [], obj=self.cli_context)

        # Verify - Click handles missing required argument
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
