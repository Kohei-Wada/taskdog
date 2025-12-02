"""Tests for pause command."""

from taskdog.cli.commands.pause import pause_command
from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.presentation.cli.commands.batch_command_test_base import BaseBatchCommandTest


class TestPauseCommand(BaseBatchCommandTest):
    """Test cases for pause command."""

    command_func = pause_command
    use_case_path = "presentation.cli.commands.pause.TaskController"
    controller_method = "pause_task"
    controller_attr = "api_client"
    action_verb = "Paused"
    action_name = "pause"

    def test_pause_in_progress_task_success(self):
        """Test pausing an in-progress task successfully."""
        # Setup
        task_before = Task(
            id=1, name="Test Task", priority=5, status=TaskStatus.IN_PROGRESS
        )
        paused_task = Task(
            id=1, name="Test Task", priority=5, status=TaskStatus.PENDING
        )

        self.repository.get_by_id.return_value = task_before
        self.api_client.pause_task.return_value = paused_task

        # Execute
        result = self.runner.invoke(pause_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.pause_task.assert_called_once()
        self.console_writer.task_success.assert_called_once_with("Paused", paused_task)
        # Verify time tracking reset message
        info_calls = [call[0][0] for call in self.console_writer.info.call_args_list]
        assert any("Time tracking has been reset" in msg for msg in info_calls)

    def test_pause_already_pending_task(self):
        """Test pausing a task that is already pending."""
        # Setup
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.PENDING)

        self.repository.get_by_id.return_value = task
        self.api_client.pause_task.return_value = task

        # Execute
        result = self.runner.invoke(pause_command, ["1"], obj=self.cli_context)

        # Verify
        assert result.exit_code == 0
        self.api_client.pause_task.assert_called_once()
        # Should show info message about time tracking reset
        self.console_writer.info.assert_called_once()
        info_msg = self.console_writer.info.call_args[0][0]
        assert "Time tracking has been reset" in info_msg
