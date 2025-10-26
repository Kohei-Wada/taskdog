"""Vi-style CommandPalette with j/k navigation."""

from typing import ClassVar

from textual.binding import Binding
from textual.command import CommandPalette
from textual.widgets import OptionList


class ViCommandPalette(CommandPalette):
    """CommandPalette with Vi-style keybindings (Ctrl+j/k for navigation)."""

    BINDINGS: ClassVar = [
        *CommandPalette.BINDINGS,
        Binding("ctrl+j", "vi_cursor_down", "Down", show=False, priority=True),
        Binding("ctrl+k", "vi_cursor_up", "Up", show=False, priority=True),
    ]

    def action_vi_cursor_down(self) -> None:
        """Move cursor down (Ctrl+j)."""
        command_list = self.query_one("CommandList", OptionList)
        command_list.action_cursor_down()

    def action_vi_cursor_up(self) -> None:
        """Move cursor up (Ctrl+k)."""
        command_list = self.query_one("CommandList", OptionList)
        command_list.action_cursor_up()
