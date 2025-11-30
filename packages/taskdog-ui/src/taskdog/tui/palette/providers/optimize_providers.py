"""Command providers for optimization functionality."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from taskdog.tui.palette.providers.base import BaseListProvider

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


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
            (
                "Optimize",
                app.search_optimize,
                "Optimize schedule with selected algorithm",
            ),
        ]
