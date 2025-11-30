"""Event handler registry for WebSocket messages.

This module provides a registry pattern for dispatching WebSocket events
to their appropriate handlers, replacing if-elif chains with a lookup table.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class EventHandlerRegistry:
    """Registry for WebSocket event handlers.

    This class maps event types to handler methods, providing a clean
    dispatch mechanism for incoming WebSocket messages.
    """

    def __init__(self, app: "TaskdogTUI"):
        """Initialize the event handler registry.

        Args:
            app: The TaskdogTUI application instance
        """
        self.app = app
        self._handlers: dict[str, Callable[[dict[str, Any]], None]] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all event handlers."""
        self._handlers["connected"] = self._handle_connected
        self._handlers["task_created"] = self._handle_task_created
        self._handlers["task_updated"] = self._handle_task_updated
        self._handlers["task_deleted"] = self._handle_task_deleted
        self._handlers["task_status_changed"] = self._handle_task_status_changed
        self._handlers["schedule_optimized"] = self._handle_schedule_optimized

    def dispatch(self, message: dict[str, Any]) -> None:
        """Dispatch event to registered handler.

        Args:
            message: WebSocket message dictionary with type and data fields
        """
        event_type = message.get("type")
        if isinstance(event_type, str) and (handler := self._handlers.get(event_type)):
            handler(message)

    def _handle_connected(self, message: dict[str, Any]) -> None:
        """Handle WebSocket connection message.

        Sets the client ID in the API client for message attribution.

        Args:
            message: Connection message with client_id
        """
        client_id = message.get("client_id")
        if client_id:
            self.app.api_client.set_client_id(client_id)

    def _handle_task_created(self, message: dict[str, Any]) -> None:
        """Handle task created event."""
        self._reload_tasks()
        task_name = message.get("task_name", "Unknown")
        task_id = message.get("task_id")
        display_source = self._get_display_source(message)
        msg = self._build_task_message(
            "added", task_name, task_id=task_id, source_client_id=display_source
        )
        self.app.notify(msg, severity="information")

    def _handle_task_updated(self, message: dict[str, Any]) -> None:
        """Handle task updated event."""
        self._reload_tasks()
        task_name = message.get("task_name", "Unknown")
        task_id = message.get("task_id")
        display_source = self._get_display_source(message)
        fields = message.get("updated_fields", [])
        details = ", ".join(fields)
        msg = self._build_task_message(
            "updated",
            task_name,
            task_id=task_id,
            details=details,
            source_client_id=display_source,
        )
        self.app.notify(msg, severity="information")

    def _handle_task_deleted(self, message: dict[str, Any]) -> None:
        """Handle task deleted event."""
        self._reload_tasks()
        task_name = message.get("task_name", "Unknown")
        task_id = message.get("task_id")
        display_source = self._get_display_source(message)
        msg = self._build_task_message(
            "deleted", task_name, task_id=task_id, source_client_id=display_source
        )
        self.app.notify(msg, severity="warning")

    def _handle_task_status_changed(self, message: dict[str, Any]) -> None:
        """Handle task status changed event."""
        self._reload_tasks()
        task_name = message.get("task_name", "Unknown")
        task_id = message.get("task_id")
        display_source = self._get_display_source(message)
        old_status = message.get("old_status", "")
        new_status = message.get("new_status", "")
        details = f"{old_status} → {new_status}"
        msg = self._build_task_message(
            "status changed",
            task_name,
            task_id=task_id,
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

        self._reload_tasks()
        scheduled_count = message.get("scheduled_count", 0)
        failed_count = message.get("failed_count", 0)
        algorithm = message.get("algorithm", "unknown")
        msg = TUIMessageBuilder.schedule_optimized(
            algorithm, scheduled_count, failed_count
        )
        self.app.notify(msg, severity="information")

    def _reload_tasks(self) -> None:
        """Reload tasks via TaskUIManager."""
        if self.app.task_ui_manager:
            self.app.call_later(
                self.app.task_ui_manager.load_tasks, keep_scroll_position=True
            )

    def _get_display_source(self, message: dict[str, Any]) -> str | None:
        """Get display source client ID if different from this client.

        Args:
            message: Message containing source_client_id

        Returns:
            Source client ID if different from this client, None otherwise
        """
        source_client_id = message.get("source_client_id")
        if (
            isinstance(source_client_id, str)
            and source_client_id != self.app.api_client.client_id
        ):
            return source_client_id
        return None

    def _build_task_message(
        self,
        action: str,
        task_name: str,
        task_id: int | None = None,
        details: str | None = None,
        source_client_id: str | None = None,
    ) -> str:
        """Build task event notification message.

        Args:
            action: Action performed (added, updated, deleted, status changed)
            task_name: Name of the task
            task_id: Optional task ID
            details: Optional additional details
            source_client_id: Optional source client ID

        Returns:
            Formatted notification message
        """
        from taskdog.tui.messages import TUIMessageBuilder

        return TUIMessageBuilder.websocket_event(
            action,
            task_name,
            task_id=task_id,
            details=details or "",
            source_client_id=source_client_id,
        )
