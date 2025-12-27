"""ViOptionList widget with Vi-style key bindings."""

from typing import ClassVar

from textual.binding import Binding
from textual.widgets import OptionList

from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin


class ViOptionList(OptionList, ViNavigationMixin):
    """OptionList with Vi-style key bindings.

    Extends Textual's OptionList to add Vi-style navigation:
    - j: Move cursor down
    - k: Move cursor up
    - g: Jump to top
    - G: Jump to bottom

    Example:
        >>> options = [Option("Item 1"), Option("Item 2")]
        >>> option_list = ViOptionList(*options)
    """

    # Use Vi vertical navigation bindings from mixin
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = list(
        ViNavigationMixin.VI_VERTICAL_BINDINGS
    )

    def action_vi_down(self) -> None:
        """Move cursor down (j key)."""
        if self.highlighted is not None:
            max_index = len(self._options) - 1
            if self.highlighted < max_index:
                self.highlighted += 1

    def action_vi_up(self) -> None:
        """Move cursor up (k key)."""
        if self.highlighted is not None and self.highlighted > 0:
            self.highlighted -= 1

    def action_vi_home(self) -> None:
        """Move to top (g key)."""
        if len(self._options) > 0:
            self.highlighted = 0

    def action_vi_end(self) -> None:
        """Move to bottom (G key)."""
        if len(self._options) > 0:
            self.highlighted = len(self._options) - 1
