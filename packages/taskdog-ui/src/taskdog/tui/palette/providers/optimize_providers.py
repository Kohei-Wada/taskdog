"""Command providers for optimization functionality."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

from taskdog.tui.palette.providers.base import BaseListProvider

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


# Command metadata: (command_name, help_text, force_override)
OPTIMIZE_COMMANDS: list[tuple[str, str, bool]] = [
    ("Optimize", "Optimize schedule with selected algorithm", False),
    ("Optimize (force)", "Force optimize schedule (override existing)", True),
]


class OptimizeCommandProvider(BaseListProvider):
    """Command provider for optimization commands."""

    def get_options(self, app: TaskdogTUI) -> list[tuple[str, Callable[[], None], str]]:
        """Return optimize command options with callbacks.

        Args:
            app: TaskdogTUI application instance

        Returns:
            List of (command_name, callback, help_text) tuples
        """
        return [
            (command_name, partial(app.search_optimize, force_override), help_text)
            for command_name, help_text, force_override in OPTIMIZE_COMMANDS
        ]
