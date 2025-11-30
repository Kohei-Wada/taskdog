"""WebSocket message handler for TUI.

This module provides WebSocket message handling logic separated from
the main app class for better separation of concerns.
"""

from typing import TYPE_CHECKING, Any

from taskdog.tui.services.event_handler_registry import EventHandlerRegistry

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class WebSocketHandler:
    """Handles incoming WebSocket messages for the TUI.

    This class receives WebSocket messages and delegates processing
    to the EventHandlerRegistry for dispatch.
    """

    def __init__(self, app: "TaskdogTUI"):
        """Initialize the WebSocket handler.

        Args:
            app: The TaskdogTUI application instance
        """
        self.app = app
        self.registry = EventHandlerRegistry(app)

    def handle_message(self, message: dict[str, Any]) -> None:
        """Handle incoming WebSocket messages.

        Args:
            message: WebSocket message dictionary with type and data fields
        """
        self.registry.dispatch(message)
