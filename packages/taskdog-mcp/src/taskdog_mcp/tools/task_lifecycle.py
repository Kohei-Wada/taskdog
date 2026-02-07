"""Task lifecycle MCP tools.

Tools for changing task status (start, complete, pause, cancel, reopen).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from taskdog_client import TaskdogApiClient


def register_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register task lifecycle tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Taskdog API client
    """

    @mcp.tool()
    def start_task(task_id: int) -> dict[str, Any]:
        """Start working on a task.

        Changes status from PENDING to IN_PROGRESS and records start time.

        Args:
            task_id: ID of the task to start

        Returns:
            Updated task data with status change confirmation
        """
        result = client.start_task(task_id)
        return {
            "id": result.id,
            "name": result.name,
            "status": result.status.value,
            "actual_start": result.actual_start.isoformat()
            if result.actual_start
            else None,
            "message": f"Task '{result.name}' started",
        }

    @mcp.tool()
    def complete_task(task_id: int) -> dict[str, Any]:
        """Mark a task as completed.

        Changes status to COMPLETED and records end time.

        Args:
            task_id: ID of the task to complete

        Returns:
            Updated task data with completion confirmation
        """
        result = client.complete_task(task_id)
        return {
            "id": result.id,
            "name": result.name,
            "status": result.status.value,
            "actual_end": result.actual_end.isoformat() if result.actual_end else None,
            "actual_duration_hours": result.actual_duration_hours,
            "message": f"Task '{result.name}' completed",
        }

    @mcp.tool()
    def pause_task(task_id: int) -> dict[str, Any]:
        """Pause a task (reset to PENDING).

        Changes status back to PENDING and clears timestamps.

        Args:
            task_id: ID of the task to pause

        Returns:
            Updated task data
        """
        result = client.pause_task(task_id)
        return {
            "id": result.id,
            "name": result.name,
            "status": result.status.value,
            "message": f"Task '{result.name}' paused",
        }

    @mcp.tool()
    def cancel_task(task_id: int) -> dict[str, Any]:
        """Cancel a task.

        Changes status to CANCELED.

        Args:
            task_id: ID of the task to cancel

        Returns:
            Updated task data
        """
        result = client.cancel_task(task_id)
        return {
            "id": result.id,
            "name": result.name,
            "status": result.status.value,
            "message": f"Task '{result.name}' canceled",
        }

    @mcp.tool()
    def reopen_task(task_id: int) -> dict[str, Any]:
        """Reopen a completed or canceled task.

        Changes status back to PENDING.

        Args:
            task_id: ID of the task to reopen

        Returns:
            Updated task data
        """
        result = client.reopen_task(task_id)
        return {
            "id": result.id,
            "name": result.name,
            "status": result.status.value,
            "message": f"Task '{result.name}' reopened",
        }

    @mcp.tool()
    def fix_actual_times(
        task_id: int,
        actual_start: str | None = None,
        actual_end: str | None = None,
        actual_duration: float | None = None,
        clear_start: bool = False,
        clear_end: bool = False,
        clear_duration: bool = False,
    ) -> dict[str, Any]:
        """Fix actual start/end timestamps for a task.

        Used to correct timestamps for historical accuracy. Past dates allowed.

        Args:
            task_id: ID of the task to fix
            actual_start: New actual start in ISO format (e.g., '2025-12-13T09:00:00')
            actual_end: New actual end in ISO format (e.g., '2025-12-13T17:00:00')
            actual_duration: Explicit duration in hours (e.g., 0.5 = 30min, 1.5 = 1h30m)
            clear_start: Clear actual_start timestamp
            clear_end: Clear actual_end timestamp
            clear_duration: Clear actual_duration (use calculated value)

        Returns:
            Updated task data with new timestamps
        """
        try:
            start_dt = datetime.fromisoformat(actual_start) if actual_start else None
            end_dt = datetime.fromisoformat(actual_end) if actual_end else None
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {e}") from e

        if actual_duration is not None and actual_duration <= 0:
            raise ValueError("actual_duration must be greater than 0")

        result = client.fix_actual_times(
            task_id=task_id,
            actual_start=start_dt,
            actual_end=end_dt,
            actual_duration=actual_duration,
            clear_start=clear_start,
            clear_end=clear_end,
            clear_duration=clear_duration,
        )

        return {
            "id": result.id,
            "name": result.name,
            "status": result.status.value,
            "actual_start": result.actual_start.isoformat()
            if result.actual_start
            else None,
            "actual_end": result.actual_end.isoformat() if result.actual_end else None,
            "actual_duration_hours": result.actual_duration_hours,
            "message": f"Fixed actual times for task '{result.name}'",
        }
