"""Tests for done command."""

from taskdog.cli.commands.done import done_command
from taskdog_core.shared.constants import StatusVerbs
from tests.presentation.cli.commands.bulk_command_test_base import (
    BaseBulkCommandTest,
    make_success_result,
)


class TestDoneCommand(BaseBulkCommandTest):
    """Test cases for done command."""

    command_func = done_command
    bulk_method = "bulk_complete"
    action_verb = StatusVerbs.COMPLETED

    def test_complete_shows_completion_details(self):
        """Test that done command shows completion details."""
        result_item = make_success_result(1)
        self._set_bulk_return([result_item])

        result = self.runner.invoke(done_command, ["1"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.task_completion_details.assert_called_once_with(
            result_item.task
        )
