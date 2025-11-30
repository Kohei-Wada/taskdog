"""Help command for TUI - displays keybindings and usage instructions."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.dialogs.help_dialog import HelpDialog


class ShowHelpCommand(TUICommandBase):
    """Command to show the help screen with keybindings and usage instructions."""

    def execute_impl(self) -> None:
        """Execute the show help command."""
        # Push help dialog modal
        help_dialog = HelpDialog()
        self.app.push_screen(help_dialog)
