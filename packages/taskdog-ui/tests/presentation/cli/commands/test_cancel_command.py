"""Tests for cancel command."""

from taskdog.cli.commands.cancel import cancel_command
from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.presentation.cli.commands.batch_command_test_base import BaseBatchCommandTest


class TestCancelCommand(BaseBatchCommandTest):
    """Test cases for cancel command."""

    command_func = cancel_command
    use_case_path = "presentation.cli.commands.cancel.TaskController"
    controller_method = "cancel_task"
    controller_attr = "api_client"
    action_verb = "Canceled"
    action_name = "cancel"

    def test_cancel_in_progress_task(self):
        """Test canceling a task that is in progress."""
        # Setup
        canceled_task = Task(
            id=1, name="Test Task", priority=5, status=TaskStatus.CANCELED
        )
        self.api_client.cancel_task.return_value = canceled_task

        # Execute
        result = self.runner.invoke(cancel_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.task_success.assert_called_once_with(
            "Canceled", canceled_task
        )
