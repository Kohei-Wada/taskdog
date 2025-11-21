"""Analytics and optimization client."""

from datetime import datetime

from taskdog.infrastructure.api.base_client import BaseApiClient
from taskdog.infrastructure.api.converters import (
    convert_to_optimization_output,
    convert_to_simulation_result,
    convert_to_statistics_output,
)
from taskdog_core.application.dto.optimization_output import OptimizationOutput
from taskdog_core.application.dto.simulation_result import SimulationResult
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
        response = self._base._safe_request(
            "get", f"/api/v1/statistics?period={period}"
        )
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_statistics_output(data)

    def optimize_schedule(
        self,
        algorithm: str,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool = True,
    ) -> OptimizationOutput:
        """Optimize task schedules.

        Args:
            algorithm: Algorithm name
            start_date: Optimization start date
            max_hours_per_day: Maximum hours per day
            force_override: Force override existing schedules

        Returns:
            OptimizationOutput with optimization results

        Raises:
            TaskValidationError: If validation fails
        """
        payload = {
            "algorithm": algorithm,
            "start_date": start_date.isoformat(),
            "max_hours_per_day": max_hours_per_day,
            "force_override": force_override,
        }

        response = self._base._safe_request("post", "/api/v1/optimize", json=payload)
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_optimization_output(data)

    def get_algorithm_metadata(self) -> list[tuple[str, str, str]]:
        """Get available optimization algorithms.

        Returns:
            List of (name, display_name, description) tuples
        """
        response = self._base._safe_request("get", "/api/v1/algorithms")
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return [
            (algo["name"], algo["display_name"], algo["description"]) for algo in data
        ]

    def simulate_task(
        self,
        estimated_duration: float,
        priority: int = 5,
        name: str = "Simulated Task",
        deadline: datetime | None = None,
        depends_on: list[int] | None = None,
        algorithm: str = "greedy",
        max_hours_per_day: float = 6.0,
        start_date: datetime | None = None,
        force_override: bool = False,
    ) -> SimulationResult:
        """Simulate a virtual task without saving to database.

        Args:
            estimated_duration: Estimated duration in hours (required)
            priority: Task priority (default: 5)
            name: Task name for display (default: "Simulated Task")
            deadline: Optional deadline
            depends_on: List of task IDs this depends on
            algorithm: Optimization algorithm to use (default: "greedy")
            max_hours_per_day: Maximum hours per day (default: 6.0)
            start_date: Optimization start date (defaults to now)
            force_override: Override existing schedules (default: False)

        Returns:
            SimulationResult with schedule prediction and workload analysis

        Raises:
            TaskValidationError: If validation fails
        """
        payload = {
            "estimated_duration": estimated_duration,
            "name": name,
            "priority": priority,
            "deadline": deadline.isoformat() if deadline else None,
            "depends_on": depends_on or [],
            "algorithm_name": algorithm,
            "max_hours_per_day": max_hours_per_day,
            "start_date": start_date.isoformat() if start_date else None,
            "force_override": force_override,
        }

        response = self._base._safe_request("post", "/api/v1/simulate", json=payload)
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_simulation_result(data)
