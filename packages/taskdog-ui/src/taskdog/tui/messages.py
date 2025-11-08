"""Textual messages for TUI events.

This module defines custom Textual messages used for reactive UI updates.
These messages enable unidirectional data flow: State → Event → View.
"""

from __future__ import annotations

from textual.message import Message


class UIUpdateRequested(Message):
    """Message to notify widgets that state has changed and UI should update.

    This message is posted to the message queue when AppState is modified.
    Widgets listen for this message and pull fresh data from AppState to re-render.

    This implements the unidirectional data flow pattern:
    1. User action → Command
    2. Command → Update AppState
    3. AppState → Post UIUpdateRequested
    4. UIUpdateRequested → Widgets pull from AppState and re-render

    Attributes:
        source_action: Optional description of what triggered the update (for debugging).
    """

    def __init__(self, source_action: str | None = None) -> None:
        """Initialize UIUpdateRequested message.

        Args:
            source_action: Optional description of what triggered this update.
        """
        super().__init__()
        self.source_action = source_action
