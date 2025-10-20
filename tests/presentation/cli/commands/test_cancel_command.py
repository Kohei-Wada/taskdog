"""Tests for cancel command."""

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskAlreadyFinishedError, TaskNotFoundException
from presentation.cli.commands.cancel import cancel_command


class TestCancelCommand(unittest.TestCase):
    """Test cases for cancel command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.repository = MagicMock()
        self.time_tracker = MagicMock()
        self.console_writer = MagicMock()
        self.config = MagicMock()

        # Set up CLI context
        self.cli_context = MagicMock()
        self.cli_context.repository = self.repository
        self.cli_context.time_tracker = self.time_tracker
        self.cli_context.console_writer = self.console_writer
        self.cli_context.config = self.config

    @patch("presentation.cli.commands.cancel.CancelTaskUseCase")
    def test_cancel_single_task_success(self, mock_use_case_class):
        """Test canceling a single task successfully."""
        # Setup
        canceled_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.CANCELED)

        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.return_value = canceled_task

        # Execute
        result = self.runner.invoke(cancel_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        mock_use_case.execute.assert_called_once()
        self.console_writer.task_success.assert_called_once_with("Canceled", canceled_task)

    @patch("presentation.cli.commands.cancel.CancelTaskUseCase")
    def test_cancel_multiple_tasks_success(self, mock_use_case_class):
        """Test canceling multiple tasks successfully."""
        # Setup
        canceled_tasks = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.CANCELED),
            Task(id=2, name="Task 2", priority=5, status=TaskStatus.CANCELED),
        ]

        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = canceled_tasks

        # Execute
        result = self.runner.invoke(cancel_command, ["1", "2"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_use_case.execute.call_count, 2)
        self.assertEqual(self.console_writer.task_success.call_count, 2)
        # Verify spacing added for multiple tasks
        self.assertEqual(self.console_writer.empty_line.call_count, 2)

    @patch("presentation.cli.commands.cancel.CancelTaskUseCase")
    def test_cancel_in_progress_task(self, mock_use_case_class):
        """Test canceling a task that is in progress."""
        # Setup
        canceled_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.CANCELED)

        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.return_value = canceled_task

        # Execute
        result = self.runner.invoke(cancel_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.task_success.assert_called_once_with("Canceled", canceled_task)

    @patch("presentation.cli.commands.cancel.CancelTaskUseCase")
    def test_cancel_nonexistent_task(self, mock_use_case_class):
        """Test canceling a task that doesn't exist."""
        # Setup
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(cancel_command, ["999"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("999", error_msg)

    @patch("presentation.cli.commands.cancel.CancelTaskUseCase")
    def test_cancel_already_finished_task(self, mock_use_case_class):
        """Test canceling a task that is already finished."""
        # Setup
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskAlreadyFinishedError(1, "COMPLETED")

        # Execute
        result = self.runner.invoke(cancel_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("task 1", error_msg)
        self.assertIn("COMPLETED", error_msg)

    @patch("presentation.cli.commands.cancel.CancelTaskUseCase")
    def test_cancel_general_exception(self, mock_use_case_class):
        """Test handling of general exception during cancellation."""
        # Setup
        mock_use_case = mock_use_case_class.return_value
        error = ValueError("Something went wrong")
        mock_use_case.execute.side_effect = error

        # Execute
        result = self.runner.invoke(cancel_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("cancel", error)

    def test_cancel_no_task_id_provided(self):
        """Test cancel command without providing task ID."""
        # Execute
        result = self.runner.invoke(cancel_command, [], obj=self.cli_context)

        # Verify - Click handles missing required argument
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
