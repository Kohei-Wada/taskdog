"""Base class for scrollable dialogs with Vi navigation."""

from abc import abstractmethod
from typing import ClassVar

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.css.query import NoMatches

from taskdog.tui.dialogs.base_dialog import BaseModalDialog
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin


class ScrollableDialogBase[T](BaseModalDialog[T], ViNavigationMixin):
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
        except NoMatches as e:
            raise RuntimeError(
                f"Scroll container '{self.scroll_container_id}' not found or "
                f"not a VerticalScroll widget in {self.__class__.__name__}"
            ) from e

    def _get_active_scroll_widget(self) -> VerticalScroll:
        """Return the single scroll container for Vi navigation.

        Plugs into ViNavigationMixin's action_vi_* methods. Raises (via
        _get_scroll_widget) if the container is misconfigured.
        """
        return self._get_scroll_widget()
