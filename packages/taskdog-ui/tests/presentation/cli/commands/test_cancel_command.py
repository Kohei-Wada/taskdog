"""Tests for cancel command."""

from taskdog.cli.commands.cancel import cancel_command
from taskdog_core.shared.constants import StatusVerbs
from tests.presentation.cli.commands.bulk_command_test_base import BaseBulkCommandTest


class TestCancelCommand(BaseBulkCommandTest):
    """Test cases for cancel command."""

    command_func = cancel_command
    bulk_method = "bulk_cancel"
    action_verb = StatusVerbs.CANCELED
