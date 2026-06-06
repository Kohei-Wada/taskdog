"""WebSocket message handler for TUI.

This module provides WebSocket message handling logic separated from
the main app class for better separation of concerns.
"""

from collections.abc import Callable
from typing import Any

from taskdog.tui.services.event_handler_registry import (
    EventHandlerRegistry,
    NotifyFn,
)


class WebSocketHandler:
    """Handles incoming WebSocket messages for the TUI.

    This class receives WebSocket messages and delegates processing
    to the EventHandlerRegistry for dispatch.
    """

    def __init__(
        self,
        *,
        notify: NotifyFn,
        reload_tasks: Callable[[], None],
        set_client_id: Callable[[str], None],
        get_client_id: Callable[[], str | None],
    ) -> None:
        """Initialize the WebSocket handler.

        Args:
            notify: Show a notification to the user.
            reload_tasks: Trigger the app's debounced task-list reload.
            set_client_id: Record this client's ID (from the connected event).
            get_client_id: Read this client's current ID.
        """
        self.registry = EventHandlerRegistry(
            notify=notify,
            reload_tasks=reload_tasks,
            set_client_id=set_client_id,
            get_client_id=get_client_id,
        )

    def handle_message(self, message: dict[str, Any]) -> None:
        """Handle incoming WebSocket messages.

        Args:
            message: WebSocket message dictionary with type and data fields
        """
        self.registry.dispatch(message)
