"""Help command for TUI - displays keybindings and usage instructions."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.screens.help_screen import HelpScreen


@command_registry.register("show_help")
class ShowHelpCommand(TUICommandBase):
    """Command to show the help screen with keybindings and usage instructions."""

    def execute_impl(self) -> None:
        """Execute the show help command."""
        # Push help screen modal
        help_screen = HelpScreen()
        self.app.push_screen(help_screen)
