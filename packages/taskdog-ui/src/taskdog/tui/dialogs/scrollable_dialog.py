"""Base class for scrollable dialogs with Vi navigation."""

from abc import abstractmethod
from typing import ClassVar, TypeVar

from textual.binding import Binding
from textual.containers import VerticalScroll

from taskdog.tui.dialogs.base_dialog import BaseModalDialog
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin

T = TypeVar("T")


class ScrollableDialogBase(BaseModalDialog[T], ViNavigationMixin):
    """Base class for scrollable read-only dialogs with Vi navigation.

    Provides:
    - Vi-style scrolling (j/k for line, Ctrl+D/U for page, g/G for home/end)
    - 'q' key to close (same as escape)

    Subclasses must:
    - Implement scroll_container_id property to specify the scroll widget ID
    - Implement compose() to define the dialog layout with a VerticalScroll widget
    """

    BINDINGS: ClassVar = [
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        Binding("q", "cancel", "Close", tooltip="Close the dialog"),
    ]

    @property
    @abstractmethod
    def scroll_container_id(self) -> str:
        """Return the ID of the scroll container.

        Example: '#detail-content' or '#help-content'
        """
        ...

    def _get_scroll_widget(self) -> VerticalScroll:
        """Get the scroll widget for navigation.

        Returns:
            The VerticalScroll widget for this dialog.

        Raises:
            RuntimeError: If scroll container is not found or not a VerticalScroll.
        """
        try:
            return self.query_one(self.scroll_container_id, VerticalScroll)
        except Exception as e:
            raise RuntimeError(
                f"Scroll container '{self.scroll_container_id}' not found or "
                f"not a VerticalScroll widget in {self.__class__.__name__}"
            ) from e

    def action_vi_down(self) -> None:
        """Scroll down one line (j key)."""
        self._get_scroll_widget().scroll_relative(y=1, animate=False)

    def action_vi_up(self) -> None:
        """Scroll up one line (k key)."""
        self._get_scroll_widget().scroll_relative(y=-1, animate=False)

    def action_vi_page_down(self) -> None:
        """Scroll down half page (Ctrl+D)."""
        scroll_widget = self._get_scroll_widget()
        scroll_widget.scroll_relative(y=scroll_widget.size.height // 2, animate=False)

    def action_vi_page_up(self) -> None:
        """Scroll up half page (Ctrl+U)."""
        scroll_widget = self._get_scroll_widget()
        scroll_widget.scroll_relative(
            y=-(scroll_widget.size.height // 2), animate=False
        )

    def action_vi_home(self) -> None:
        """Scroll to top (g key)."""
        self._get_scroll_widget().scroll_home(animate=False)

    def action_vi_end(self) -> None:
        """Scroll to bottom (G key)."""
        self._get_scroll_widget().scroll_end(animate=False)
