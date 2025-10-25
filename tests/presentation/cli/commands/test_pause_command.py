"""Tests for pause command."""

import unittest
from unittest.mock import patch

from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskAlreadyFinishedError, TaskNotFoundException
from presentation.cli.commands.pause import pause_command
from tests.presentation.cli.commands.base_command_test import BaseBatchCommandTest


class TestPauseCommand(BaseBatchCommandTest):
    """Test cases for pause command."""

    @patch("presentation.cli.commands.pause.PauseTaskUseCase")
    def test_pause_in_progress_task_success(self, mock_use_case_class):
        """Test pausing an in-progress task successfully."""
        # Setup
        task_before = Task(id=1, name="Test Task", priority=5, status=TaskStatus.IN_PROGRESS)
        paused_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.PENDING)

        self.repository.get_by_id.return_value = task_before
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.return_value = paused_task

        # Execute
        result = self.runner.invoke(pause_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        mock_use_case.execute.assert_called_once()
        self.console_writer.task_success.assert_called_once_with("Paused", paused_task)
        # Verify time tracking reset message
        info_calls = [call[0][0] for call in self.console_writer.info.call_args_list]
        self.assertTrue(any("Time tracking has been reset" in msg for msg in info_calls))

    @patch("presentation.cli.commands.pause.PauseTaskUseCase")
    def test_pause_already_pending_task(self, mock_use_case_class):
        """Test pausing a task that is already pending."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.PENDING)

        self.repository.get_by_id.return_value = task
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.return_value = task

        # Execute
        result = self.runner.invoke(pause_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        mock_use_case.execute.assert_called_once()
        # Should show info message that task was already pending
        self.console_writer.info.assert_called_once()
        info_msg = self.console_writer.info.call_args[0][0]
        self.assertIn("already PENDING", info_msg)

    @patch("presentation.cli.commands.pause.PauseTaskUseCase")
    def test_pause_multiple_tasks_success(self, mock_use_case_class):
        """Test pausing multiple tasks successfully."""
        # Setup
        tasks_before = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.IN_PROGRESS),
            Task(id=2, name="Task 2", priority=5, status=TaskStatus.IN_PROGRESS),
        ]
        paused_tasks = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.PENDING),
            Task(id=2, name="Task 2", priority=5, status=TaskStatus.PENDING),
        ]

        self.repository.get_by_id.side_effect = tasks_before
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = paused_tasks

        # Execute
        result = self.runner.invoke(pause_command, ["1", "2"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_use_case.execute.call_count, 2)
        self.assertEqual(self.console_writer.task_success.call_count, 2)
        # Verify spacing added for multiple tasks
        self.assertEqual(self.console_writer.empty_line.call_count, 2)

    @patch("presentation.cli.commands.pause.PauseTaskUseCase")
    def test_pause_nonexistent_task(self, mock_use_case_class):
        """Test pausing a task that doesn't exist."""
        # Setup
        self.repository.get_by_id.return_value = None
        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(pause_command, ["999"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("999", error_msg)

    @patch("presentation.cli.commands.pause.PauseTaskUseCase")
    def test_pause_finished_task(self, mock_use_case_class):
        """Test pausing a task that is already finished."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.COMPLETED)
        self.repository.get_by_id.return_value = task

        mock_use_case = mock_use_case_class.return_value
        mock_use_case.execute.side_effect = TaskAlreadyFinishedError(1, "COMPLETED")

        # Execute
        result = self.runner.invoke(pause_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("task 1", error_msg)
        self.assertIn("COMPLETED", error_msg)

    @patch("presentation.cli.commands.pause.PauseTaskUseCase")
    def test_pause_general_exception(self, mock_use_case_class):
        """Test handling of general exception during pause."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.IN_PROGRESS)
        self.repository.get_by_id.return_value = task

        mock_use_case = mock_use_case_class.return_value
        error = ValueError("Something went wrong")
        mock_use_case.execute.side_effect = error

        # Execute
        result = self.runner.invoke(pause_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with("pause", error)

    def test_pause_no_task_id_provided(self):
        """Test pause command without providing task ID."""
        # Execute
        result = self.runner.invoke(pause_command, [], obj=self.cli_context)

        # Verify - Click handles missing required argument
        self.assertNotEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
