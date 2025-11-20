"""Base widget class with TUI app state access helpers.

This module provides a mixin class for widgets that need type-safe
access to the TUI application state.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI
    from taskdog.tui.state import TUIState


class TUIWidget:
    """Mixin class for TUI widgets with app state access helpers.

    This mixin provides type-safe property accessors for the TUI app
    and its state, eliminating the need for repeated type: ignore comments
    throughout widget code.

    Example:
        class MyWidget(DataTable, TUIWidget):
            def my_method(self):
                # Clean, type-safe access to app state
                viewmodels = self.tui_state.filtered_viewmodels
                sort_field = self.tui_state.sort_by
    """

    @property
    def tui_app(self) -> "TaskdogTUI":
        """Get typed reference to TaskdogTUI app.

        Returns:
            The TaskdogTUI application instance

        Note:
            This property assumes the widget is mounted in a TaskdogTUI app.
            Using it before mounting or in a different app context will
            result in incorrect typing (though the runtime app will still work).

        Raises:
            RuntimeError: If the widget is not mounted or app is None
        """
        if not hasattr(self, "app") or self.app is None:
            raise RuntimeError(
                "Widget must be mounted in a TUI app before accessing tui_app"
            )
        return self.app  # type: ignore[no-any-return]

    @property
    def tui_state(self) -> "TUIState":
        """Get reference to TUI state.

        Returns:
            The TUIState instance from the app

        Note:
            This is a convenience property equivalent to self.tui_app.state
        """
        return self.tui_app.state
