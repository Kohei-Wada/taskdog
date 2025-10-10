"""Base dialog class for TUI modal screens."""

from abc import abstractmethod
from typing import ClassVar, TypeVar

from textual.screen import ModalScreen

T = TypeVar("T")


class BaseModalDialog(ModalScreen[T]):
    """Base class for modal dialog screens.

    Provides common functionality:
    - Escape key to cancel (dismiss with None)
    - Centered alignment (applied via CSS)
    - Standard dialog structure

    Subclasses should:
    - Implement compose() to define the dialog layout
    - Override on_mount() if custom initialization is needed
    - Call dismiss(result) when ready to close
    """

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
    ]

    def action_cancel(self) -> None:
        """Cancel and close the dialog (Escape key).

        By default, dismisses with None. Override if different behavior is needed.
        """
        self.dismiss(None)

    @abstractmethod
    def compose(self):
        """Compose the dialog layout.

        Must be implemented by subclasses.
        """
        ...
