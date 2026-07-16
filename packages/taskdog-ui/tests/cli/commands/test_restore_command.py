"""Tests for restore command."""

from tests.cli.commands.bulk_command_test_base import BaseBulkCommandTest

from taskdog.cli.commands.restore import restore_command
from taskdog_core.shared.constants import StatusVerbs


class TestRestoreCommand(BaseBulkCommandTest):
    """Test cases for restore command."""

    command_func = restore_command
    bulk_method = "bulk_restore"
    action_verb = StatusVerbs.RESTORED
