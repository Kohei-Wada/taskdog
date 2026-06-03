"""Vi-style navigation mixin for TUI widgets.

Provides Vi-style keybindings AND their default scroll behavior. Scroll-based
widgets only need to implement ``_get_active_scroll_widget()``; the action
methods here delegate to it. Cursor-based consumers (e.g. Select overlays,
DataTables) override the ``action_vi_*`` methods instead.
"""

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding

if TYPE_CHECKING:
    from textual.containers import VerticalScroll


class ViNavigationMixin:
    """Mixin providing Vi-style keybindings and scroll behavior.

    Binding sets are exposed as class variables so widgets can compose the
    subset they need into their own ``BINDINGS``. The ``action_vi_*`` methods
    implement the default (scroll-based) behavior, delegating to
    ``_get_active_scroll_widget()``.
    """

    # Basic vertical navigation (j/k for up/down, g/G for top/bottom)
    VI_VERTICAL_BINDINGS: ClassVar = [
        Binding(
            "j", "vi_down", "Down", show=False, tooltip="Move cursor down (Vi-style)"
        ),
        Binding("k", "vi_up", "Up", show=False, tooltip="Move cursor up (Vi-style)"),
        Binding("g", "vi_home", "Top", show=False, tooltip="Jump to top (Vi-style)"),
        Binding(
            "G", "vi_end", "Bottom", show=False, tooltip="Jump to bottom (Vi-style)"
        ),
    ]

    # Half-page scrolling
    VI_PAGE_BINDINGS: ClassVar = [
        Binding(
            "ctrl+d",
            "vi_page_down",
            "Page Down",
            show=False,
            tooltip="Scroll down half a page (Vi-style)",
        ),
        Binding(
            "ctrl+u",
            "vi_page_up",
            "Page Up",
            show=False,
            tooltip="Scroll up half a page (Vi-style)",
        ),
    ]

    # Horizontal scrolling
    VI_HORIZONTAL_BINDINGS: ClassVar = [
        Binding(
            "h",
            "vi_scroll_left",
            "Scroll Left",
            show=False,
            tooltip="Scroll left (Vi-style)",
        ),
        Binding(
            "l",
            "vi_scroll_right",
            "Scroll Right",
            show=False,
            tooltip="Scroll right (Vi-style)",
        ),
    ]

    # Horizontal jump to edges
    VI_HORIZONTAL_JUMP_BINDINGS: ClassVar = [
        Binding(
            "0",
            "vi_home_horizontal",
            "Scroll to Leftmost",
            show=False,
            tooltip="Jump to leftmost position (Vi-style)",
        ),
        Binding(
            "$",
            "vi_end_horizontal",
            "Scroll to Rightmost",
            show=False,
            tooltip="Jump to rightmost position (Vi-style)",
        ),
    ]

    def _get_active_scroll_widget(self) -> "VerticalScroll | None":
        """Return the scroll widget the vi actions should act on.

        Default returns None (actions become no-ops). Scroll-based subclasses
        override this; cursor-based consumers override the action_vi_* methods.
        """
        return None

    def action_vi_down(self) -> None:
        """Scroll down one line (j key)."""
        if (widget := self._get_active_scroll_widget()) is not None:
            widget.scroll_relative(y=1, animate=False)

    def action_vi_up(self) -> None:
        """Scroll up one line (k key)."""
        if (widget := self._get_active_scroll_widget()) is not None:
            widget.scroll_relative(y=-1, animate=False)

    def action_vi_page_down(self) -> None:
        """Scroll down half a page (Ctrl+D)."""
        if (widget := self._get_active_scroll_widget()) is not None:
            widget.scroll_relative(y=widget.size.height // 2, animate=False)

    def action_vi_page_up(self) -> None:
        """Scroll up half a page (Ctrl+U)."""
        if (widget := self._get_active_scroll_widget()) is not None:
            widget.scroll_relative(y=-(widget.size.height // 2), animate=False)

    def action_vi_home(self) -> None:
        """Scroll to top (g key)."""
        if (widget := self._get_active_scroll_widget()) is not None:
            widget.scroll_home(animate=False)

    def action_vi_end(self) -> None:
        """Scroll to bottom (G key)."""
        if (widget := self._get_active_scroll_widget()) is not None:
            widget.scroll_end(animate=False)
