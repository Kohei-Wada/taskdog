"""Broadcast helper for WebSocket notifications.

This module provides helper functions to broadcast task change events
to all connected WebSocket clients.
"""

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_server.websocket.connection_manager import ConnectionManager


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
    await manager.broadcast(
        {
            "type": "task_created",
            "task_id": task.id,
            "task_name": task.name,
            "priority": task.priority,
            "status": task.status.value,
            "source_client_id": exclude_client_id,
        },
        exclude_client_id=exclude_client_id,
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
    await manager.broadcast(
        {
            "type": "task_updated",
            "task_id": task.id,
            "task_name": task.name,
            "updated_fields": fields,
            "status": task.status.value,
            "source_client_id": exclude_client_id,
        },
        exclude_client_id=exclude_client_id,
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
    await manager.broadcast(
        {
            "type": "task_deleted",
            "task_id": task_id,
            "task_name": task_name,
            "source_client_id": exclude_client_id,
        },
        exclude_client_id=exclude_client_id,
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
    await manager.broadcast(
        {
            "type": "task_status_changed",
            "task_id": task.id,
            "task_name": task.name,
            "old_status": old_status,
            "new_status": task.status.value,
            "source_client_id": exclude_client_id,
        },
        exclude_client_id=exclude_client_id,
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
    await manager.broadcast(
        {
            "type": "task_updated",
            "task_id": task_id,
            "task_name": task_name,
            "updated_fields": ["notes"],
            "source_client_id": exclude_client_id,
        },
        exclude_client_id=exclude_client_id,
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
    await manager.broadcast(
        {
            "type": "schedule_optimized",
            "scheduled_count": scheduled_count,
            "failed_count": failed_count,
            "algorithm": algorithm,
            "source_client_id": exclude_client_id,
        },
        exclude_client_id=exclude_client_id,
    )
