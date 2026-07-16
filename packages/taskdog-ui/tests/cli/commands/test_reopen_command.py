"""Tests for reopen command."""

from tests.cli.commands.bulk_command_test_base import BaseBulkCommandTest

from taskdog.cli.commands.reopen import reopen_command
from taskdog_core.shared.constants import StatusVerbs


class TestReopenCommand(BaseBulkCommandTest):
    """Test cases for reopen command."""

    command_func = reopen_command
    bulk_method = "bulk_reopen"
    action_verb = StatusVerbs.REOPENED
