"""Tests for CommandFactory."""

from unittest.mock import Mock

from taskdog.tui.commands.factory import CommandFactory
from taskdog.tui.context import TUIContext


class TestCommandFactory:
    """Test cases for CommandFactory."""

    def setup_method(self):
        self.mock_app = Mock()
        self.mock_context = Mock(spec=TUIContext)
        self.factory = CommandFactory(app=self.mock_app, context=self.mock_context)

    def test_create_returns_command_for_known_name(self):
        command = self.factory.create("refresh")
        assert command is not None

    def test_create_returns_none_for_unknown_name(self):
        command = self.factory.create("nonexistent_command")
        assert command is None

    def test_execute_calls_command_execute(self):
        mock_command = Mock()
        self.factory.create = Mock(return_value=mock_command)

        self.factory.execute("refresh")

        mock_command.execute.assert_called_once()

    def test_execute_does_nothing_for_unknown_command(self):
        self.factory.execute("nonexistent_command")
