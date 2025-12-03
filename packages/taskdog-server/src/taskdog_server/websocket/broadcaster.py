"""WebSocket event broadcaster for task notifications.

This module provides a unified class for broadcasting task change events
to all connected WebSocket clients via FastAPI background tasks.
"""

from collections.abc import Callable
from typing import Any

from fastapi import BackgroundTasks

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_server.websocket.connection_manager import ConnectionManager


class WebSocketEventBroadcaster:
    """Unified event broadcaster for WebSocket notifications.

    Centralizes event broadcasting logic and schedules broadcasts
    as FastAPI background tasks for non-blocking API responses.
    """

    def __init__(
        self, manager: ConnectionManager, background_tasks: BackgroundTasks
    ) -> None:
        """Initialize event broadcaster.

        Args:
            manager: ConnectionManager instance for WebSocket communication
            background_tasks: FastAPI background tasks for async scheduling
        """
        self._manager = manager
        self._background_tasks = background_tasks

    def add_background_task(
        self, func: Callable[..., Any], *args: object, **kwargs: object
    ) -> None:
        """Add a task to run in the background.

        Provides public access to schedule background tasks for
        non-broadcast operations that need background execution.

        Args:
            func: The function to run in the background
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        self._background_tasks.add_task(func, *args, **kwargs)

    def task_created(
        self,
        task: TaskOperationOutput,
        source_user_name: str | None = None,
    ) -> None:
        """Schedule a task creation broadcast.

        Args:
            task: The created task DTO
            source_user_name: User name who triggered the event (for payload info)
        """
        payload = {
            "task_id": task.id,
            "task_name": task.name,
            "priority": task.priority,
            "status": task.status.value,
        }
        self._schedule_broadcast("task_created", payload, source_user_name)

    def task_updated(
        self,
        task: TaskOperationOutput,
        fields: list[str],
        source_user_name: str | None = None,
    ) -> None:
        """Schedule a task update broadcast.

        Args:
            task: The updated task DTO
            fields: List of updated field names
            source_user_name: User name who triggered the event (for payload info)
        """
        payload = {
            "task_id": task.id,
            "task_name": task.name,
            "updated_fields": fields,
            "status": task.status.value,
        }
        self._schedule_broadcast("task_updated", payload, source_user_name)

    def task_deleted(
        self,
        task_id: int,
        task_name: str,
        source_user_name: str | None = None,
    ) -> None:
        """Schedule a task deletion broadcast.

        Args:
            task_id: The deleted task ID
            task_name: The deleted task name
            source_user_name: User name who triggered the event (for payload info)
        """
        payload = {
            "task_id": task_id,
            "task_name": task_name,
        }
        self._schedule_broadcast("task_deleted", payload, source_user_name)

    def task_status_changed(
        self,
        task: TaskOperationOutput,
        old_status: str,
        source_user_name: str | None = None,
    ) -> None:
        """Schedule a task status change broadcast.

        Args:
            task: The task DTO with new status
            old_status: The previous status value
            source_user_name: User name who triggered the event (for payload info)
        """
        payload = {
            "task_id": task.id,
            "task_name": task.name,
            "old_status": old_status,
            "new_status": task.status.value,
        }
        self._schedule_broadcast("task_status_changed", payload, source_user_name)

    def task_notes_updated(
        self,
        task_id: int,
        task_name: str,
        source_user_name: str | None = None,
    ) -> None:
        """Schedule a task notes update broadcast.

        Args:
            task_id: The task ID
            task_name: The task name
            source_user_name: User name who triggered the event (for payload info)
        """
        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "updated_fields": ["notes"],
        }
        self._schedule_broadcast("task_updated", payload, source_user_name)

    def schedule_optimized(
        self,
        scheduled_count: int,
        failed_count: int,
        algorithm: str,
        source_user_name: str | None = None,
    ) -> None:
        """Schedule a schedule optimization broadcast.

        Args:
            scheduled_count: Number of successfully scheduled tasks
            failed_count: Number of failed tasks
            algorithm: Algorithm used for optimization
            source_user_name: User name who triggered the event (for payload info)
        """
        payload = {
            "scheduled_count": scheduled_count,
            "failed_count": failed_count,
            "algorithm": algorithm,
        }
        self._schedule_broadcast("schedule_optimized", payload, source_user_name)

    def _schedule_broadcast(
        self,
        event_type: str,
        payload: dict[str, Any],
        source_user_name: str | None = None,
    ) -> None:
        """Schedule a broadcast as a background task.

        Args:
            event_type: The type of event (e.g., "task_created")
            payload: Event-specific data to broadcast
            source_user_name: User name who triggered the event (for payload info)
        """
        self._background_tasks.add_task(
            self._broadcast, event_type, payload, source_user_name
        )

    async def _broadcast(
        self,
        event_type: str,
        payload: dict[str, Any],
        source_user_name: str | None = None,
    ) -> None:
        """Broadcast an event to all connected clients.

        Args:
            event_type: The type of event
            payload: Event-specific data
            source_user_name: User name who triggered the event (for payload info)
        """
        broadcast_payload = payload.copy()
        broadcast_payload["type"] = event_type
        broadcast_payload["source_user_name"] = source_user_name
        await self._manager.broadcast(broadcast_payload)
