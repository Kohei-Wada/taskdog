"""Tests for cancel command."""

from tests.cli.commands.bulk_command_test_base import BaseBulkCommandTest

from taskdog.cli.commands.cancel import cancel_command
from taskdog_core.shared.constants import StatusVerbs


class TestCancelCommand(BaseBulkCommandTest):
    """Test cases for cancel command."""

    command_func = cancel_command
    bulk_method = "bulk_cancel"
    action_verb = StatusVerbs.CANCELED
