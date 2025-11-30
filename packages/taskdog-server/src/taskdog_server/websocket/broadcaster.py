"""Broadcast helper for WebSocket notifications.

This module provides helper functions to broadcast task change events
to all connected WebSocket clients.
"""

from typing import Any

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_server.websocket.connection_manager import ConnectionManager


class EventBroadcaster:
    """Centralized event broadcaster for WebSocket notifications.

    Reduces code duplication by providing a common method for broadcasting
    events with standard fields (type, source_client_id).
    """

    def __init__(self, manager: ConnectionManager) -> None:
        """Initialize event broadcaster.

        Args:
            manager: ConnectionManager instance for WebSocket communication
        """
        self._manager = manager

    async def broadcast_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        exclude_client_id: str | None = None,
    ) -> None:
        """Broadcast an event with common fields.

        Args:
            event_type: The type of event (e.g., "task_created", "task_updated")
            payload: Event-specific data to broadcast
            exclude_client_id: Optional client ID to exclude from broadcast
        """
        broadcast_payload = payload.copy()
        broadcast_payload["type"] = event_type
        broadcast_payload["source_client_id"] = exclude_client_id
        await self._manager.broadcast(broadcast_payload, exclude_client_id)


async def broadcast_task_created(
    manager: ConnectionManager,
    task: TaskOperationOutput,
    exclude_client_id: str | None = None,
) -> None:
    """Broadcast task creation event.

    Args:
        manager: ConnectionManager instance
        task: The created task DTO
        exclude_client_id: Optional client ID to exclude from broadcast
    """
    broadcaster = EventBroadcaster(manager)
    await broadcaster.broadcast_event(
        "task_created",
        {
            "task_id": task.id,
            "task_name": task.name,
            "priority": task.priority,
            "status": task.status.value,
        },
        exclude_client_id,
    )


async def broadcast_task_updated(
    manager: ConnectionManager,
    task: TaskOperationOutput,
    fields: list[str],
    exclude_client_id: str | None = None,
) -> None:
    """Broadcast task update event.

    Args:
        manager: ConnectionManager instance
        task: The updated task DTO
        fields: List of updated field names
        exclude_client_id: Optional client ID to exclude from broadcast
    """
    broadcaster = EventBroadcaster(manager)
    await broadcaster.broadcast_event(
        "task_updated",
        {
            "task_id": task.id,
            "task_name": task.name,
            "updated_fields": fields,
            "status": task.status.value,
        },
        exclude_client_id,
    )


async def broadcast_task_deleted(
    manager: ConnectionManager,
    task_id: int,
    task_name: str,
    exclude_client_id: str | None = None,
) -> None:
    """Broadcast task deletion event.

    Args:
        manager: ConnectionManager instance
        task_id: The deleted task ID
        task_name: The deleted task name
        exclude_client_id: Optional client ID to exclude from broadcast
    """
    broadcaster = EventBroadcaster(manager)
    await broadcaster.broadcast_event(
        "task_deleted",
        {
            "task_id": task_id,
            "task_name": task_name,
        },
        exclude_client_id,
    )


async def broadcast_task_status_changed(
    manager: ConnectionManager,
    task: TaskOperationOutput,
    old_status: str,
    exclude_client_id: str | None = None,
) -> None:
    """Broadcast task status change event.

    Args:
        manager: ConnectionManager instance
        task: The task DTO with new status
        old_status: The previous status value
        exclude_client_id: Optional client ID to exclude from broadcast
    """
    broadcaster = EventBroadcaster(manager)
    await broadcaster.broadcast_event(
        "task_status_changed",
        {
            "task_id": task.id,
            "task_name": task.name,
            "old_status": old_status,
            "new_status": task.status.value,
        },
        exclude_client_id,
    )


async def broadcast_task_notes_updated(
    manager: ConnectionManager,
    task_id: int,
    task_name: str,
    exclude_client_id: str | None = None,
) -> None:
    """Broadcast task notes update event.

    Args:
        manager: ConnectionManager instance
        task_id: The task ID
        task_name: The task name
        exclude_client_id: Optional client ID to exclude from broadcast
    """
    broadcaster = EventBroadcaster(manager)
    await broadcaster.broadcast_event(
        "task_updated",
        {
            "task_id": task_id,
            "task_name": task_name,
            "updated_fields": ["notes"],
        },
        exclude_client_id,
    )


async def broadcast_schedule_optimized(
    manager: ConnectionManager,
    scheduled_count: int,
    failed_count: int,
    algorithm: str,
    exclude_client_id: str | None = None,
) -> None:
    """Broadcast schedule optimization event.

    Args:
        manager: ConnectionManager instance
        scheduled_count: Number of successfully scheduled tasks
        failed_count: Number of failed tasks
        algorithm: Algorithm used for optimization
        exclude_client_id: Optional client ID to exclude from broadcast
    """
    broadcaster = EventBroadcaster(manager)
    await broadcaster.broadcast_event(
        "schedule_optimized",
        {
            "scheduled_count": scheduled_count,
            "failed_count": failed_count,
            "algorithm": algorithm,
        },
        exclude_client_id,
    )
