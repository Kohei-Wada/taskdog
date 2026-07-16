"""Tests for the Gantt filter command provider."""

from taskdog.tui.app import TaskdogTUI
from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider
from taskdog.tui.palette.providers.gantt_filter_provider import (
    GanttFilterCommandProvider,
)


class TestGanttFilterCommandProvider:
    """Test cases for GanttFilterCommandProvider."""

    def test_inherits_simple_single_command_provider(self):
        """Test that GanttFilterCommandProvider uses SimpleSingleCommandProvider."""
        assert issubclass(GanttFilterCommandProvider, SimpleSingleCommandProvider)

    def test_command_attributes(self):
        """Test that class attributes are correctly defined."""
        assert GanttFilterCommandProvider.COMMAND_NAME == "Toggle Gantt Filter"
        assert (
            GanttFilterCommandProvider.COMMAND_CALLBACK_NAME
            == "action_toggle_gantt_filter"
        )
        assert len(GanttFilterCommandProvider.COMMAND_HELP) > 0

    def test_callback_exists_on_app(self):
        """Test that the configured callback is a real method on the app."""
        assert hasattr(TaskdogTUI, GanttFilterCommandProvider.COMMAND_CALLBACK_NAME)

    def test_registered_in_app_commands(self):
        """Test that the provider is registered in the command palette."""
        assert GanttFilterCommandProvider in TaskdogTUI.COMMANDS
