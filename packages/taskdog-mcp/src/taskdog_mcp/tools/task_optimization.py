"""Task optimization MCP tools.

Tools for auto-generating optimal task schedules and listing available
optimization algorithms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taskdog_mcp.tools.serializers import parse_iso_datetime

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
    from taskdog_client import TaskdogApiClient


def register_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register task optimization tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Taskdog API client
    """

    @mcp.tool()
    def optimize_schedule(
        algorithm: str,
        max_hours_per_day: float,
        start_date: str | None = None,
        task_ids: list[int] | None = None,
        force_override: bool = False,
        include_all_days: bool = False,
    ) -> dict[str, Any]:
        """Auto-generate optimal task schedules.

        Schedules tasks with estimated_duration based on priority, deadlines,
        and dependencies. By default schedules on weekdays only and skips tasks
        that already have a planned_start (use force_override to override).

        Args:
            algorithm: Algorithm name. One of: greedy (front-load),
                balanced (even distribution), backward (JIT from deadline),
                priority_first (priority only), earliest_deadline (EDF),
                round_robin (parallel progress), dependency_aware (CPM),
                genetic (evolutionary), monte_carlo (random sampling).
                Use list_algorithms() to discover available algorithms.
            max_hours_per_day: Maximum work hours per day (e.g., 6.0 or 8.0)
            start_date: Optimization start date in ISO format
                (e.g., '2025-12-15' or '2025-12-15T09:00:00').
                Defaults to server current time when omitted.
            task_ids: Specific task IDs to optimize. If omitted, all
                schedulable tasks are considered.
            force_override: If True, override existing schedules
            include_all_days: If True, schedule on weekends and holidays too

        Returns:
            Optimization result with successful_tasks, failed_tasks,
            daily_allocations, and summary metrics.
        """
        start_dt = parse_iso_datetime(start_date, "start_date")

        if max_hours_per_day <= 0:
            raise ValueError("max_hours_per_day must be greater than 0")

        result = client.optimize_schedule(
            algorithm=algorithm,
            start_date=start_dt,
            max_hours_per_day=max_hours_per_day,
            force_override=force_override,
            task_ids=task_ids,
            include_all_days=include_all_days,
        )

        successful = [{"id": t.id, "name": t.name} for t in result.successful_tasks]
        failed = [
            {"id": f.task.id, "name": f.task.name, "reason": f.reason}
            for f in result.failed_tasks
        ]

        if result.all_failed():
            message = (
                f"All {len(failed)} task(s) failed to be scheduled with '{algorithm}'"
            )
        elif result.has_failures():
            message = (
                f"Optimized {len(successful)} task(s) using '{algorithm}' "
                f"({len(failed)} could not be scheduled)"
            )
        elif len(successful) == 0:
            message = (
                "No tasks were optimized "
                "(all tasks already scheduled, no estimated_duration, "
                "or all completed)"
            )
        else:
            message = (
                f"Optimized {len(successful)} task(s) using '{algorithm}' "
                "(all tasks scheduled)"
            )

        return {
            "algorithm": algorithm,
            "successful_tasks": successful,
            "failed_tasks": failed,
            "daily_allocations": {
                d.isoformat(): hours for d, hours in result.daily_allocations.items()
            },
            "summary": {
                "new_count": result.summary.new_count,
                "rescheduled_count": result.summary.rescheduled_count,
                "total_hours": result.summary.total_hours,
                "deadline_conflicts": result.summary.deadline_conflicts,
                "days_span": result.summary.days_span,
                "overloaded_days": [
                    {"date": d, "hours": h} for d, h in result.summary.overloaded_days
                ],
            },
            "message": message,
        }

    @mcp.tool()
    def list_algorithms() -> dict[str, Any]:
        """List available schedule optimization algorithms.

        Returns metadata for each algorithm so callers can choose one
        appropriate for their workload.

        Returns:
            Dict with `algorithms` (list of {name, display_name, description})
            and `total` count.
        """
        metadata = client.get_algorithm_metadata()
        algorithms = [
            {"name": name, "display_name": display_name, "description": description}
            for name, display_name, description in metadata
        ]
        return {
            "algorithms": algorithms,
            "total": len(algorithms),
        }
