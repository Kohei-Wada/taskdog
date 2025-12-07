"""Task query MCP tools.

Tools for querying task information (statistics, today's tasks, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from taskdog_mcp.server import TaskdogMcpClients


def register_tools(mcp: FastMCP, clients: TaskdogMcpClients) -> None:
    """Register task query tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        clients: API clients container
    """

    @mcp.tool()
    def get_statistics(period: str = "all") -> dict[str, Any]:
        """Get task statistics.

        Args:
            period: Time period for statistics (all, 7d, 30d)

        Returns:
            Statistics including counts by status, completion rates, etc.
        """
        result = clients.analytics.calculate_statistics(period)
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
    def get_today_tasks(
        status: str | None = None,
        sort_by: str = "deadline",
    ) -> dict[str, Any]:
        """Get tasks relevant for today.

        Includes:
        - Tasks with deadline today
        - Tasks with planned period including today
        - Tasks currently IN_PROGRESS

        Args:
            status: Filter by status (PENDING, IN_PROGRESS, COMPLETED, CANCELED)
            sort_by: Sort field (default: deadline)

        Returns:
            Today's tasks list
        """
        result = clients.queries.list_today_tasks(
            status=status,
            sort_by=sort_by,
        )
        return {
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority,
                    "deadline": t.deadline.isoformat() if t.deadline else None,
                    "estimated_duration": t.estimated_duration,
                    "tags": list(t.tags) if t.tags else [],
                }
                for t in result.tasks
            ],
            "total": result.filtered_count,
        }

    @mcp.tool()
    def get_week_tasks(
        status: str | None = None,
        sort_by: str = "deadline",
    ) -> dict[str, Any]:
        """Get tasks relevant for this week.

        Includes:
        - Tasks with deadline within this week (Monday to Sunday)
        - Tasks with planned period overlapping this week
        - Tasks currently IN_PROGRESS

        Args:
            status: Filter by status
            sort_by: Sort field (default: deadline)

        Returns:
            This week's tasks list
        """
        result = clients.queries.list_week_tasks(
            status=status,
            sort_by=sort_by,
        )
        return {
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority,
                    "deadline": t.deadline.isoformat() if t.deadline else None,
                    "estimated_duration": t.estimated_duration,
                    "tags": list(t.tags) if t.tags else [],
                }
                for t in result.tasks
            ],
            "total": result.filtered_count,
        }

    @mcp.tool()
    def get_tag_statistics() -> dict[str, Any]:
        """Get statistics for all tags.

        Returns:
            Tag statistics including task counts per tag
        """
        result = clients.queries.get_tag_statistics()
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
        pending = clients.queries.list_tasks(
            status="pending",
            tags=tags,
            sort_by="priority",
            reverse=True,  # Higher priority first
        )

        in_progress = clients.queries.list_tasks(
            status="in_progress",
            tags=tags,
            sort_by="priority",
            reverse=True,
        )

        # Combine and limit
        all_tasks = list(in_progress.tasks) + list(pending.tasks)
        limited_tasks = all_tasks[:limit]

        return {
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority,
                    "deadline": t.deadline.isoformat() if t.deadline else None,
                    "estimated_duration": t.estimated_duration,
                    "tags": list(t.tags) if t.tags else [],
                    "depends_on": list(t.depends_on) if t.depends_on else [],
                }
                for t in limited_tasks
            ],
            "total": len(limited_tasks),
            "message": f"Found {len(limited_tasks)} executable tasks (IN_PROGRESS tasks shown first)",
        }
