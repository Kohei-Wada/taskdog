"""Command providers for task simulation functionality."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from taskdog.tui.palette.providers.base import BaseListProvider

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class SimulateCommandProvider(BaseListProvider):
    """Command provider for task simulation."""

    def get_options(self, app: TaskdogTUI) -> list[tuple[str, Callable[[], None], str]]:
        """Return simulate command option with callback.

        Args:
            app: TaskdogTUI application instance

        Returns:
            List of (command_name, callback, help_text) tuples
        """
        return [
            (
                "Simulate Task",
                app.search_simulate,
                "Simulate a task to predict completion date without saving",
            )
        ]
