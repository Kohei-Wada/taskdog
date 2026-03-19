"""Tests for pause command."""

from taskdog.cli.commands.pause import pause_command
from taskdog_core.shared.constants import StatusVerbs
from tests.presentation.cli.commands.bulk_command_test_base import (
    BaseBulkCommandTest,
    make_success_result,
)


class TestPauseCommand(BaseBulkCommandTest):
    """Test cases for pause command."""

    command_func = pause_command
    bulk_method = "bulk_pause"
    action_verb = StatusVerbs.PAUSED

    def test_pause_shows_time_tracking_reset(self):
        """Test that pause command shows time tracking reset info."""
        result_item = make_success_result(1)
        self._set_bulk_return([result_item])

        result = self.runner.invoke(pause_command, ["1"], obj=self.cli_context)

        assert result.exit_code == 0
        self.console_writer.info.assert_called_once()
        info_msg = self.console_writer.info.call_args[0][0]
        assert "Time tracking has been reset" in info_msg
