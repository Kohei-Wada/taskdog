"""Task query MCP tools.

Tools for querying task information (statistics, today's tasks, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_mcp.tools.serializers import iso, str_list

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
    from taskdog_client import TaskdogApiClient


def _dependencies_met(
    depends_on: list[int],
    client: TaskdogApiClient,
    dep_status_cache: dict[int, TaskStatus | None],
) -> bool:
    """Check whether all dependency ids are COMPLETED.

    A missing dependency (e.g. its task was deleted) counts as unmet,
    matching DependencyValidator.validate_dependencies_met semantics.
    Statuses are memoized in dep_status_cache so a dep shared across
    multiple tasks is only fetched once per get_executable_tasks call.
    """
    for dep_id in depends_on:
        if dep_id not in dep_status_cache:
            try:
                dep_status_cache[dep_id] = client.get_task_by_id(dep_id).task.status
            except TaskNotFoundException:
                dep_status_cache[dep_id] = None
        if dep_status_cache[dep_id] != TaskStatus.COMPLETED:
            return False
    return True


def _select_executable_pending(
    pending_tasks: list[Any],
    client: TaskdogApiClient,
    max_count: int,
) -> list[Any]:
    """Filter pending tasks down to those whose dependencies are met.

    Stops scanning once max_count executable tasks have been found, so
    dependency lookups for tasks beyond the eventual limit are skipped.
    """
    dep_status_cache: dict[int, TaskStatus | None] = {}
    executable_pending: list[Any] = []
    for t in pending_tasks:
        if len(executable_pending) >= max_count:
            break
        if not t.depends_on or _dependencies_met(
            t.depends_on, client, dep_status_cache
        ):
            executable_pending.append(t)
    return executable_pending


def register_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register task query tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Taskdog API client
    """

    @mcp.tool()
    def get_statistics(period: str = "all") -> dict[str, Any]:
        """Get task statistics.

        Args:
            period: Time period for statistics (all, 7d, 30d)

        Returns:
            Statistics including counts by status, completion rates, etc.
        """
        result = client.calculate_statistics(period)
        # StatisticsOutput has .task_stats, .time_stats, etc.
        task_stats = result.task_stats
        time_stats = result.time_stats
        return {
            "period": period,
            "total_tasks": task_stats.total_tasks,
            "pending": task_stats.pending_count,
            "in_progress": task_stats.in_progress_count,
            "completed": task_stats.completed_count,
            "canceled": task_stats.canceled_count,
            "completion_rate": task_stats.completion_rate,
            "overdue_count": 0,  # Not directly available
            "average_completion_time_hours": time_stats.average_work_hours
            if time_stats
            else None,
        }

    @mcp.tool()
    def get_tag_statistics() -> dict[str, Any]:
        """Get statistics for all tags.

        Returns:
            Tag statistics including task counts per tag
        """
        result = client.get_tag_statistics()
        # TagStatisticsOutput has .tag_counts (dict), .total_tags (int)
        return {
            "tags": [
                {"tag": tag, "count": count} for tag, count in result.tag_counts.items()
            ],
            "total_tags": result.total_tags,
        }

    @mcp.tool()
    def get_executable_tasks(
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Get tasks that AI can potentially execute.

        Returns PENDING or IN_PROGRESS tasks sorted by priority.
        Use this to find tasks to work on.

        Args:
            tags: Filter by tags (e.g., ['coding', 'ai-executable'])
            limit: Maximum number of tasks to return

        Returns:
            List of executable tasks with details
        """
        # Get pending and in-progress tasks
        pending = client.list_tasks(
            status="pending",
            tags=tags,
            sort_by="priority",
            reverse=True,  # Higher priority first
        )

        in_progress = client.list_tasks(
            status="in_progress",
            tags=tags,
            sort_by="priority",
            reverse=True,
        )

        # Filter out pending tasks with unmet dependencies, stopping once
        # enough executable tasks are found to fill the remaining limit.
        remaining_slots = max(limit - len(in_progress.tasks), 0)
        executable_pending = _select_executable_pending(
            pending.tasks, client, remaining_slots
        )

        # Combine and limit
        all_tasks = list(in_progress.tasks) + executable_pending
        limited_tasks = all_tasks[:limit]

        return {
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority,
                    "deadline": iso(t.deadline),
                    "estimated_duration": t.estimated_duration,
                    "tags": str_list(t.tags),
                    "depends_on": str_list(t.depends_on),
                }
                for t in limited_tasks
            ],
            "total": len(limited_tasks),
            "message": f"Found {len(limited_tasks)} executable tasks (IN_PROGRESS tasks shown first)",
        }
