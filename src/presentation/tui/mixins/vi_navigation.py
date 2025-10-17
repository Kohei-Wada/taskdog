"""Vi-style navigation mixin for TUI widgets."""

from typing import ClassVar


class ViNavigationMixin:
    """Mixin that adds Vi-style navigation key bindings.

    Provides standard Vi-style navigation keys:
    - j: Move cursor down
    - k: Move cursor up
    - g: Jump to top
    - G: Jump to bottom

    Widgets using this mixin must implement:
    - action_cursor_down()
    - action_cursor_up()
    - action_scroll_home()
    - action_scroll_end()
    """

    BINDINGS: ClassVar = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("g", "scroll_home", "Top"),
        ("G", "scroll_end", "Bottom"),
    ]
