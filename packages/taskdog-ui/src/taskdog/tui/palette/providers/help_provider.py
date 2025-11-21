"""Command provider for help functionality."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from taskdog.tui.palette.providers.base import BaseListProvider

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class HelpCommandProvider(BaseListProvider):
    """Command provider for help command."""

    def get_options(self, app: TaskdogTUI) -> list[tuple[str, Callable[[], None], str]]:
        """Return help command option.

        Args:
            app: TaskdogTUI application instance

        Returns:
            List of (command_name, callback, help_text) tuples
        """
        return [
            (
                "Help",
                app.search_help,
                "Show keybindings and usage instructions",
            ),
        ]
