"""Tests for cancel command."""

import unittest
from unittest.mock import patch

from domain.entities.task import Task, TaskStatus
from presentation.cli.commands.cancel import cancel_command
from tests.presentation.cli.commands.batch_command_test_base import BaseBatchCommandTest


class TestCancelCommand(BaseBatchCommandTest):
    """Test cases for cancel command."""

    command_func = cancel_command
    use_case_path = "presentation.cli.commands.cancel.TaskController"
    controller_method = "cancel_task"
    action_verb = "Canceled"
    action_name = "cancel"

    @patch("presentation.cli.commands.cancel.TaskController")
    def test_cancel_in_progress_task(self, mock_controller_class):
        """Test canceling a task that is in progress."""
        # Setup
        canceled_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.CANCELED)

        mock_controller = mock_controller_class.return_value
        mock_controller.cancel_task.return_value = canceled_task

        # Execute
        result = self.runner.invoke(cancel_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.task_success.assert_called_once_with("Canceled", canceled_task)


if __name__ == "__main__":
    unittest.main()
