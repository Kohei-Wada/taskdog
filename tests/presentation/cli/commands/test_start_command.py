"""Tests for start command."""

import unittest

from domain.entities.task import Task, TaskStatus
from presentation.cli.commands.start import start_command
from tests.presentation.cli.commands.batch_command_test_base import BaseBatchCommandTest


class TestStartCommand(BaseBatchCommandTest):
    """Test cases for start command."""

    command_func = start_command
    use_case_path = "presentation.cli.commands.start.TaskController"
    controller_method = "start_task"
    action_verb = "Started"
    action_name = "start"

    def test_start_already_in_progress_task(self):
        """Test starting a task that is already in progress."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.IN_PROGRESS)

        self.repository.get_by_id.return_value = task
        self.task_controller.start_task.return_value = task

        # Execute
        result = self.runner.invoke(start_command, ["1"], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        # Should still show success message
        self.console_writer.task_success.assert_called_once()
        # Should indicate task was already in progress
        call_args = self.console_writer.task_start_time.call_args
        self.assertTrue(call_args[0][1])  # was_already_in_progress = True


if __name__ == "__main__":
    unittest.main()
