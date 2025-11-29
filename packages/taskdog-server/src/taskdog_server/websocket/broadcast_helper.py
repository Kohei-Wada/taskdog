"""Broadcast helper for scheduling WebSocket notifications.

This module provides a helper class to standardize the pattern of scheduling
WebSocket broadcasts as background tasks in FastAPI routers.
"""

from collections.abc import Callable
from typing import Any

from fastapi import BackgroundTasks

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_server.websocket.broadcaster import (
    broadcast_schedule_optimized,
    broadcast_task_created,
    broadcast_task_deleted,
    broadcast_task_notes_updated,
    broadcast_task_status_changed,
    broadcast_task_updated,
)
from taskdog_server.websocket.connection_manager import ConnectionManager


class BroadcastHelper:
    """Helper class for scheduling WebSocket broadcasts as background tasks.

    This class is injected via FastAPI's dependency injection system,
    reducing boilerplate code in API routers.
    """

    def __init__(
        self, manager: ConnectionManager, background_tasks: BackgroundTasks
    ) -> None:
        """Initialize broadcast helper.

        Args:
            manager: ConnectionManager instance
            background_tasks: FastAPI background tasks
        """
        self._manager = manager
        self._background_tasks = background_tasks

    def add_background_task(
        self, func: Callable[..., Any], *args: object, **kwargs: object
    ) -> None:
        """Add a task to run in the background.

        This method provides public access to schedule background tasks,
        useful for non-broadcast operations that still need background execution.

        Args:
            func: The function to run in the background
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        self._background_tasks.add_task(func, *args, **kwargs)

    def task_created(
        self,
        task: TaskOperationOutput,
        exclude_client_id: str | None = None,
    ) -> None:
        """Schedule a task creation broadcast.

        Args:
            task: The created task DTO
            exclude_client_id: Optional client ID to exclude from broadcast
        """
        self._background_tasks.add_task(
            broadcast_task_created, self._manager, task, exclude_client_id
        )

    def task_updated(
        self,
        task: TaskOperationOutput,
        fields: list[str],
        exclude_client_id: str | None = None,
    ) -> None:
        """Schedule a task update broadcast.

        Args:
            task: The updated task DTO
            fields: List of updated field names
            exclude_client_id: Optional client ID to exclude from broadcast
        """
        self._background_tasks.add_task(
            broadcast_task_updated, self._manager, task, fields, exclude_client_id
        )

    def task_deleted(
        self,
        task_id: int,
        task_name: str,
        exclude_client_id: str | None = None,
    ) -> None:
        """Schedule a task deletion broadcast.

        Args:
            task_id: The deleted task ID
            task_name: The deleted task name
            exclude_client_id: Optional client ID to exclude from broadcast
        """
        self._background_tasks.add_task(
            broadcast_task_deleted, self._manager, task_id, task_name, exclude_client_id
        )

    def task_status_changed(
        self,
        task: TaskOperationOutput,
        old_status: str,
        exclude_client_id: str | None = None,
    ) -> None:
        """Schedule a task status change broadcast.

        Args:
            task: The task DTO with new status
            old_status: The previous status value
            exclude_client_id: Optional client ID to exclude from broadcast
        """
        self._background_tasks.add_task(
            broadcast_task_status_changed,
            self._manager,
            task,
            old_status,
            exclude_client_id,
        )

    def task_notes_updated(
        self,
        task_id: int,
        task_name: str,
        exclude_client_id: str | None = None,
    ) -> None:
        """Schedule a task notes update broadcast.

        Args:
            task_id: The task ID
            task_name: The task name
            exclude_client_id: Optional client ID to exclude from broadcast
        """
        self._background_tasks.add_task(
            broadcast_task_notes_updated,
            self._manager,
            task_id,
            task_name,
            exclude_client_id,
        )

    def schedule_optimized(
        self,
        scheduled_count: int,
        failed_count: int,
        algorithm: str,
        exclude_client_id: str | None = None,
    ) -> None:
        """Schedule a schedule optimization broadcast.

        Args:
            scheduled_count: Number of successfully scheduled tasks
            failed_count: Number of failed tasks
            algorithm: Algorithm used for optimization
            exclude_client_id: Optional client ID to exclude from broadcast
        """
        self._background_tasks.add_task(
            broadcast_schedule_optimized,
            self._manager,
            scheduled_count,
            failed_count,
            algorithm,
            exclude_client_id,
        )
