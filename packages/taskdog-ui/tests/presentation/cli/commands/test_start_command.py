"""Tests for start command."""

from taskdog.cli.commands.start import start_command
from taskdog_core.shared.constants import StatusVerbs
from tests.presentation.cli.commands.bulk_command_test_base import (
    BaseBulkCommandTest,
    make_success_result,
)


class TestStartCommand(BaseBulkCommandTest):
    """Test cases for start command."""

    command_func = start_command
    bulk_method = "bulk_start"
    action_verb = StatusVerbs.STARTED

    def test_start_shows_start_time(self):
        """Test that start command shows task start time."""
        result_item = make_success_result(1)
        self._set_bulk_return([result_item])

        result = self.runner.invoke(start_command, ["1"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.task_start_time.assert_called_once_with(
            result_item.task, was_already_in_progress=False
        )
