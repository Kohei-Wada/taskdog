"""Base test class for CLI batch command tests."""

import unittest
from unittest.mock import MagicMock

from click.testing import CliRunner

from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
)


class BaseBatchCommandTest(unittest.TestCase):
    """Base test class with common setup for batch CLI commands.

    Provides common fixtures and test methods for testing commands that process
    multiple tasks (start, done, pause, cancel, etc.).

    Subclasses must override:
    - command_func: The Click command function to test
    - use_case_path: Full path to the use case/controller class for patching
    - action_verb: Past tense action verb (e.g., "Started", "Completed")
    - controller_method: Optional controller method name (e.g., "start_task", "complete_task")
                        If not set, assumes use case with execute() method
    - success_callback: Optional callback method name (e.g., "task_start_time")
    """

    # Override in subclasses
    command_func = None
    use_case_path = None
    action_verb = None  # Past tense: "Started", "Completed", "Paused", "Canceled"
    action_name = None  # Present tense for errors: "start", "complete", "pause", "cancel"
    controller_method = (
        None  # Optional: "start_task", "complete_task", etc. (for controller-based commands)
    )
    success_callback = None  # Optional: task_start_time, task_completion_details, etc.

    @classmethod
    def setUpClass(cls):
        """Skip test execution for the base class itself."""
        if cls is BaseBatchCommandTest:
            raise unittest.SkipTest("Skipping base test class")

    def setUp(self):
        """Set up common test fixtures."""
        self.runner = CliRunner()
        self.repository = MagicMock()
        self.time_tracker = MagicMock()
        self.console_writer = MagicMock()
        self.config = MagicMock()
        self.task_controller = MagicMock()
        self.query_controller = MagicMock()

        # Set up CLI context with all dependencies
        self.cli_context = MagicMock()
        self.cli_context.repository = self.repository
        self.cli_context.time_tracker = self.time_tracker
        self.cli_context.console_writer = self.console_writer
        self.cli_context.config = self.config
        self.cli_context.task_controller = self.task_controller
        self.cli_context.query_controller = self.query_controller

    def _get_mock_method(self, mock_instance):
        """Get the mock method based on controller_method or execute.

        Args:
            mock_instance: The mocked controller or use case instance

        Returns:
            The mock method to call (controller method or execute)
        """
        if self.controller_method:
            return getattr(mock_instance, self.controller_method)
        return mock_instance.execute

    def test_single_task_success(self):
        """Test executing command on a single task successfully."""
        # Setup
        result_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.COMPLETED)
        mock_method = getattr(self.task_controller, self.controller_method)
        mock_method.return_value = result_task

        # Execute
        result = self.runner.invoke(self.command_func, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        mock_method.assert_called_once()
        self.console_writer.task_success.assert_called_once_with(self.action_verb, result_task)

    def test_multiple_tasks_success(self):
        """Test executing command on multiple tasks successfully."""
        # Setup
        result_tasks = [
            Task(id=1, name="Task 1", priority=5, status=TaskStatus.COMPLETED),
            Task(id=2, name="Task 2", priority=5, status=TaskStatus.COMPLETED),
        ]
        mock_method = getattr(self.task_controller, self.controller_method)
        mock_method.side_effect = result_tasks

        # Execute
        result = self.runner.invoke(self.command_func, ["1", "2"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_method.call_count, 2)
        self.assertEqual(self.console_writer.task_success.call_count, 2)
        # Verify spacing added for multiple tasks
        self.assertEqual(self.console_writer.empty_line.call_count, 2)

    def test_nonexistent_task(self):
        """Test command with non-existent task."""
        # Setup
        mock_method = getattr(self.task_controller, self.controller_method)
        mock_method.side_effect = TaskNotFoundException(999)

        # Execute
        result = self.runner.invoke(self.command_func, ["999"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("999", error_msg)

    def test_already_finished_task(self):
        """Test command with already finished task."""
        # Setup
        mock_method = getattr(self.task_controller, self.controller_method)
        mock_method.side_effect = TaskAlreadyFinishedError(1, "COMPLETED")

        # Execute
        result = self.runner.invoke(self.command_func, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("task 1", error_msg)
        self.assertIn("COMPLETED", error_msg)

    def test_general_exception(self):
        """Test handling of general exception during command execution."""
        # Setup
        mock_method = getattr(self.task_controller, self.controller_method)
        error = ValueError("Something went wrong")
        mock_method.side_effect = error

        # Execute
        result = self.runner.invoke(self.command_func, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.error.assert_called_once_with(self.action_name, error)

    def test_no_task_id_provided(self):
        """Test command without providing task ID."""
        # Execute
        result = self.runner.invoke(self.command_func, [], obj=self.cli_context)

        # Verify - Click handles missing required argument
        self.assertNotEqual(result.exit_code, 0)
