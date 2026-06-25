"""Tests for the remaining single-command palette providers.

Mirrors ``test_gantt_filter_provider.py`` for the providers that previously
had no coverage: archive, audit, backup, and help.
"""

import pytest

from taskdog.tui.app import TaskdogTUI
from taskdog.tui.palette.providers.archive_provider import ArchiveCommandProvider
from taskdog.tui.palette.providers.audit_provider import AuditCommandProvider
from taskdog.tui.palette.providers.backup_provider import BackupCommandProvider
from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider
from taskdog.tui.palette.providers.help_provider import HelpCommandProvider
from taskdog.tui.palette.providers.stats_provider import StatsCommandProvider

PROVIDERS = [
    ArchiveCommandProvider,
    AuditCommandProvider,
    BackupCommandProvider,
    HelpCommandProvider,
    StatsCommandProvider,
]


@pytest.mark.parametrize("provider", PROVIDERS)
class TestSimpleCommandProviders:
    """Shared assertions for single-command palette providers."""

    def test_inherits_simple_single_command_provider(self, provider):
        """Test that the provider uses SimpleSingleCommandProvider."""
        assert issubclass(provider, SimpleSingleCommandProvider)

    def test_command_attributes_defined(self, provider):
        """Test that the command class attributes are defined and non-empty."""
        assert provider.COMMAND_NAME
        assert provider.COMMAND_HELP
        assert provider.COMMAND_CALLBACK_NAME

    def test_callback_exists_on_app(self, provider):
        """Test that the configured callback is a real attribute on the app."""
        assert hasattr(TaskdogTUI, provider.COMMAND_CALLBACK_NAME)

    def test_registered_in_app_commands(self, provider):
        """Test that the provider is registered in the command palette."""
        assert provider in TaskdogTUI.COMMANDS
