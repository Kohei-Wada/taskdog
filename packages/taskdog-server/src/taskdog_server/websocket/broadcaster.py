"""Broadcast helper for WebSocket notifications.

This module provides helper functions to broadcast task change events
to all connected WebSocket clients.
"""

from typing import Any

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


async def broadcast_task_created(manager: Any, task: TaskOperationOutput) -> None:
    """Broadcast task creation event.

    Args:
        manager: ConnectionManager instance
        task: The created task DTO
    """
    await manager.broadcast(
        {
            "type": "task_created",
            "task_id": task.id,
            "task_name": task.name,
            "priority": task.priority,
            "status": task.status.value,
        }
    )


async def broadcast_task_updated(
    manager: Any, task: TaskOperationOutput, fields: list[str]
) -> None:
    """Broadcast task update event.

    Args:
        manager: ConnectionManager instance
        task: The updated task DTO
        fields: List of updated field names
    """
    await manager.broadcast(
        {
            "type": "task_updated",
            "task_id": task.id,
            "task_name": task.name,
            "updated_fields": fields,
            "status": task.status.value,
        }
    )


async def broadcast_task_deleted(manager: Any, task_id: int, task_name: str) -> None:
    """Broadcast task deletion event.

    Args:
        manager: ConnectionManager instance
        task_id: The deleted task ID
        task_name: The deleted task name
    """
    await manager.broadcast(
        {
            "type": "task_deleted",
            "task_id": task_id,
            "task_name": task_name,
        }
    )


async def broadcast_task_status_changed(
    manager: Any, task: TaskOperationOutput, old_status: str
) -> None:
    """Broadcast task status change event.

    Args:
        manager: ConnectionManager instance
        task: The task DTO with new status
        old_status: The previous status value
    """
    await manager.broadcast(
        {
            "type": "task_status_changed",
            "task_id": task.id,
            "task_name": task.name,
            "old_status": old_status,
            "new_status": task.status.value,
        }
    )
