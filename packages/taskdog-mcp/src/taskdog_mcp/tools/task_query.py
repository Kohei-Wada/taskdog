"""Task query MCP tools.

Tools for querying task information (statistics, today's tasks, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taskdog_mcp.tools.serializers import iso, model_dump, str_list

if TYPE_CHECKING:
    from mcp.server import MCPServer
    from taskdog_client import TaskdogApiClient


def register_tools(mcp: MCPServer, client: TaskdogApiClient) -> None:
    """Register task query tools with the MCP server.

    Args:
        mcp: MCPServer instance
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
            "average_completion_time_hours": time_stats.average_work_hours
            if time_stats
            else None,
            # Every remaining StatisticsOutput section, serialized as-is.
            "time_stats": model_dump(time_stats),
            "estimation_stats": model_dump(result.estimation_stats),
            "deadline_stats": model_dump(result.deadline_stats),
            "priority_stats": model_dump(result.priority_stats),
            "trend_stats": model_dump(result.trend_stats),
            "activity_stats": model_dump(result.activity_stats),
            "reschedule_stats": model_dump(result.reschedule_stats),
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
        result = client.get_executable_tasks(tags=tags, limit=limit)
        tasks = result.tasks

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
                for t in tasks
            ],
            "total": len(tasks),
            "message": f"Found {len(tasks)} executable tasks (IN_PROGRESS tasks shown first)",
        }
