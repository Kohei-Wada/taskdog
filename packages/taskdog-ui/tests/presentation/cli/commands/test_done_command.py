"""Tests for done command."""

from taskdog.cli.commands.done import done_command
from taskdog_core.domain.exceptions.task_exceptions import TaskNotStartedError
from tests.presentation.cli.commands.batch_command_test_base import BaseBatchCommandTest


class TestDoneCommand(BaseBatchCommandTest):
    """Test cases for done command."""

    command_func = done_command
    use_case_path = "presentation.cli.commands.done.TaskController"
    controller_method = "complete_task"
    controller_attr = "api_client"
    action_verb = "Completed"
    action_name = "complete"

    def test_complete_not_started_task(self):
        """Test completing a task that hasn't been started."""
        # Setup
        self.api_client.complete_task.side_effect = TaskNotStartedError(1)

        # Execute
        result = self.runner.invoke(done_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()
        error_msg = self.console_writer.validation_error.call_args[0][0]
        assert "task 1" in error_msg
        assert "PENDING" in error_msg
        assert "taskdog start 1" in error_msg
