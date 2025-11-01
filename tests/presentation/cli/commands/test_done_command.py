"""Tests for done command."""

import unittest
from unittest.mock import patch

from domain.exceptions.task_exceptions import TaskNotStartedError
from presentation.cli.commands.done import done_command
from tests.presentation.cli.commands.batch_command_test_base import BaseBatchCommandTest


class TestDoneCommand(BaseBatchCommandTest):
    """Test cases for done command."""

    command_func = done_command
    use_case_path = "presentation.cli.commands.done.TaskController"
    controller_method = "complete_task"
    action_verb = "Completed"
    action_name = "complete"

    @patch("presentation.cli.commands.done.TaskController")
    def test_complete_not_started_task(self, mock_controller_class):
        """Test completing a task that hasn't been started."""
        # Setup
        mock_controller = mock_controller_class.return_value
        mock_controller.complete_task.side_effect = TaskNotStartedError(1)

        # Execute
        result = self.runner.invoke(done_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        self.assertIn("task 1", error_msg)
        self.assertIn("PENDING", error_msg)
        self.assertIn("taskdog start 1", error_msg)


if __name__ == "__main__":
    unittest.main()
