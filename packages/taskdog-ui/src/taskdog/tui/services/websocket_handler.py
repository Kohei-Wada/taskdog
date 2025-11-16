"""WebSocket message handler for TUI.

This module provides WebSocket message handling logic separated from
the main app class for better separation of concerns.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class WebSocketHandler:
    """Handles incoming WebSocket messages for the TUI.

    This class encapsulates all WebSocket message processing logic,
    delegating UI updates and notifications to the app instance.
    """

    def __init__(self, app: "TaskdogTUI"):
        """Initialize the WebSocket handler.

        Args:
            app: The TaskdogTUI application instance
        """
        self.app = app

    def handle_message(self, message: dict[str, Any]) -> None:
        """Handle incoming WebSocket messages.

        Args:
            message: WebSocket message dictionary with type and data fields
        """

        msg_type = message.get("type")

        # Handle connection message - set client ID in API client
        if msg_type == "connected":
            self._handle_connected(message)
            return

        # Handle task-related events
        if msg_type in (
            "task_created",
            "task_updated",
            "task_deleted",
            "task_status_changed",
        ):
            self._handle_task_event(message, msg_type)
        elif msg_type == "schedule_optimized":
            self._handle_schedule_optimized(message)

    def _handle_connected(self, message: dict[str, Any]) -> None:
        """Handle WebSocket connection message.

        Sets the client ID in the API client for message attribution.

        Args:
            message: Connection message with client_id
        """
        client_id = message.get("client_id")
        if client_id:
            self.app.api_client.set_client_id(client_id)

    def _handle_task_event(self, message: dict[str, Any], msg_type: str) -> None:
        """Handle task-related WebSocket events.

        Reloads tasks and shows appropriate notifications based on event type.

        Args:
            message: Task event message
            msg_type: Type of task event (created, updated, deleted, status_changed)
        """
        from taskdog.tui.messages import TUIMessageBuilder

        # Reload tasks on any task change
        self.app.call_later(self.app._load_tasks, keep_scroll_position=True)

        # Show notification with source client ID if available
        task_name = message.get("task_name", "Unknown")
        source_client_id = message.get("source_client_id")

        # Only show "by {client_id}" if the source is different from this client
        display_source = None
        if source_client_id and source_client_id != self.app.api_client.client_id:
            display_source = source_client_id

        if msg_type == "task_created":
            msg = TUIMessageBuilder.websocket_event(
                "added", task_name, source_client_id=display_source
            )
            self.app.notify(msg, severity="information")
        elif msg_type == "task_updated":
            fields = message.get("updated_fields", [])
            details = ", ".join(fields)
            msg = TUIMessageBuilder.websocket_event(
                "updated",
                task_name,
                details=details,
                source_client_id=display_source,
            )
            self.app.notify(msg, severity="information")
        elif msg_type == "task_deleted":
            msg = TUIMessageBuilder.websocket_event(
                "deleted", task_name, source_client_id=display_source
            )
            self.app.notify(msg, severity="warning")
        elif msg_type == "task_status_changed":
            old_status = message.get("old_status", "")
            new_status = message.get("new_status", "")
            details = f"{old_status} → {new_status}"
            msg = TUIMessageBuilder.websocket_event(
                "status changed",
                task_name,
                details=details,
                source_client_id=display_source,
            )
            self.app.notify(msg, severity="information")

    def _handle_schedule_optimized(self, message: dict[str, Any]) -> None:
        """Handle schedule optimization WebSocket event.

        Reloads tasks and shows optimization result notification.

        Args:
            message: Schedule optimization message with counts and algorithm
        """
        from taskdog.tui.messages import TUIMessageBuilder

        # Reload tasks on schedule optimization
        self.app.call_later(self.app._load_tasks, keep_scroll_position=True)

        # Show notification
        scheduled_count = message.get("scheduled_count", 0)
        failed_count = message.get("failed_count", 0)
        algorithm = message.get("algorithm", "unknown")
        msg = TUIMessageBuilder.schedule_optimized(
            algorithm, scheduled_count, failed_count
        )
        self.app.notify(msg, severity="information")
