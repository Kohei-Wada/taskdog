"""Vi-style navigation mixin for TUI widgets.

This module provides a mixin class for adding Vi-style keybindings to Textual widgets.
Different widget types can use appropriate binding sets based on their navigation needs.
"""

from typing import ClassVar

from textual.binding import Binding


class ViNavigationMixin:
    """Mixin providing Vi-style keybindings for navigation.

    This mixin provides common Vi-style keyboard shortcuts that can be used
    across different widget types. Widgets should:
    1. Include this mixin in their inheritance
    2. Use appropriate BINDINGS class variable sets
    3. Implement corresponding action_* methods

    The mixin provides several binding sets for different use cases:
    - VI_VERTICAL_BINDINGS: Basic vertical navigation (j/k/g/G)
    - VI_PAGE_BINDINGS: Half-page scrolling (Ctrl+d/u)
    - VI_HORIZONTAL_BINDINGS: Horizontal scrolling (h/l)
    - VI_HORIZONTAL_JUMP_BINDINGS: Jump to horizontal edges (0/$)
    - VI_ALL_BINDINGS: Complete set of all Vi bindings
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
            "dollar_sign",
            "vi_end_horizontal",
            "Scroll to Rightmost",
            show=False,
            tooltip="Jump to rightmost position (Vi-style)",
        ),
    ]

    # Complete set of all Vi bindings
    VI_ALL_BINDINGS: ClassVar = (
        VI_VERTICAL_BINDINGS
        + VI_PAGE_BINDINGS
        + VI_HORIZONTAL_BINDINGS
        + VI_HORIZONTAL_JUMP_BINDINGS
    )

    # Scroll-compatible bindings for VerticalScroll containers
    # These map to built-in scroll_* actions instead of vi_* actions
    VI_SCROLL_BINDINGS: ClassVar = [
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
    ]

    # Note: Widgets must implement action_vi_* methods corresponding to the bindings
    # they use. Default implementations are not provided as behavior varies by widget type.
    # For scroll containers, use VI_SCROLL_BINDINGS which map to built-in scroll actions.
