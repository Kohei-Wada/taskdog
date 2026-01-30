"""Analytics and optimization client."""

from datetime import datetime

from taskdog_client.base_client import BaseApiClient
from taskdog_client.converters import (
    convert_to_optimization_output,
    convert_to_statistics_output,
)
from taskdog_core.application.dto.optimization_output import OptimizationOutput
from taskdog_core.application.dto.statistics_output import StatisticsOutput


class AnalyticsClient:
    """Client for analytics and schedule optimization.

    Operations:
    - Calculate statistics
    - Optimize schedules
    - Get algorithm metadata
    """

    def __init__(self, base_client: BaseApiClient):
        """Initialize analytics client.

        Args:
            base_client: Base API client for HTTP operations
        """
        self._base = base_client

    def calculate_statistics(self, period: str = "all") -> StatisticsOutput:
        """Calculate task statistics.

        Args:
            period: Time period (all, 7d, 30d)

        Returns:
            StatisticsOutput with statistics data

        Raises:
            TaskValidationError: If period is invalid
        """
        data = self._base._request_json("get", f"/api/v1/statistics?period={period}")
        return convert_to_statistics_output(data)

    def optimize_schedule(
        self,
        algorithm: str,
        start_date: datetime | None,
        max_hours_per_day: float,
        force_override: bool = True,
        task_ids: list[int] | None = None,
        include_all_days: bool = False,
    ) -> OptimizationOutput:
        """Optimize task schedules.

        Args:
            algorithm: Algorithm name (required)
            start_date: Optimization start date (None = server current time)
            max_hours_per_day: Maximum hours per day (required)
            force_override: Force override existing schedules
            task_ids: Specific task IDs to optimize (None means all schedulable tasks)
            include_all_days: If True, schedule tasks on weekends and holidays too (default: False)

        Returns:
            OptimizationOutput with optimization results

        Raises:
            TaskValidationError: If validation fails
            TaskNotFoundException: If any specified task_id does not exist
            NoSchedulableTasksError: If no tasks can be scheduled
        """
        payload: dict[str, str | float | bool | list[int] | None] = {
            "algorithm": algorithm,
            "start_date": start_date.isoformat() if start_date else None,
            "max_hours_per_day": max_hours_per_day,
            "force_override": force_override,
            "include_all_days": include_all_days,
        }

        # Only include task_ids if it's not None
        if task_ids is not None:
            payload["task_ids"] = task_ids

        data = self._base._request_json("post", "/api/v1/optimize", json=payload)
        return convert_to_optimization_output(data)

    def get_algorithm_metadata(self) -> list[tuple[str, str, str]]:
        """Get available optimization algorithms.

        Returns:
            List of (name, display_name, description) tuples
        """
        data = self._base._request_json("get", "/api/v1/algorithms")
        return [
            (algo["name"], algo["display_name"], algo["description"]) for algo in data
        ]
