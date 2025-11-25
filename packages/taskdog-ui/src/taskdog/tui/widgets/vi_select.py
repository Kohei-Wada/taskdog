"""ViSelect widget with Vi-style key bindings."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar

from textual.binding import Binding
from textual.widgets import Select
from textual.widgets._select import SelectCurrent, SelectOverlay

from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin

if TYPE_CHECKING:
    from textual.app import ComposeResult


class ViSelectOverlay(SelectOverlay, ViNavigationMixin):
    """SelectOverlay with Vi-style key bindings.

    Extends Textual's SelectOverlay to add Vi-style navigation:
    - j: Move cursor down
    - k: Move cursor up
    - g: Jump to top
    - G: Jump to bottom
    """

    BINDINGS: ClassVar[Sequence[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        *SelectOverlay.BINDINGS,
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
    ]

    def action_vi_down(self) -> None:
        """Move cursor down (j key)."""
        self.action_cursor_down()

    def action_vi_up(self) -> None:
        """Move cursor up (k key)."""
        self.action_cursor_up()

    def action_vi_home(self) -> None:
        """Move to top (g key)."""
        self.action_first()

    def action_vi_end(self) -> None:
        """Move to bottom (G key)."""
        self.action_last()


class ViSelect(Select):  # type: ignore[type-arg]
    """Select with Vi-style key bindings for dropdown navigation.

    Extends Textual's Select to use ViSelectOverlay which adds Vi-style navigation
    when the dropdown is expanded:
    - j: Move cursor down
    - k: Move cursor up
    - g: Jump to top
    - G: Jump to bottom

    Type-to-search is disabled by default to allow Vi key bindings to work.

    Example:
        >>> options = [("Option 1", "opt1"), ("Option 2", "opt2")]
        >>> select = ViSelect(options, allow_blank=False)
    """

    def __init__(self, *args: Any, type_to_search: bool = False, **kwargs: Any) -> None:
        """Initialize ViSelect with type_to_search disabled by default.

        Type-to-search is disabled because it consumes printable key events
        (including j, k, g, G) before they can be processed as Vi keybindings.
        """
        super().__init__(*args, type_to_search=type_to_search, **kwargs)

    def compose(self) -> "ComposeResult":
        """Compose Select with Vi-enabled overlay and current value."""
        yield SelectCurrent(self.prompt)
        yield ViSelectOverlay(type_to_search=self._type_to_search).data_bind(
            compact=Select.compact
        )
