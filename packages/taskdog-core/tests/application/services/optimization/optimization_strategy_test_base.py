"""Base test class for optimization strategy tests."""

import unittest
from datetime import datetime

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.dto.optimize_schedule_input import OptimizeScheduleInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from taskdog_core.domain.entities.task import Task
from taskdog_core.shared.config_manager import ConfigManager
from tests.test_fixtures import InMemoryDatabaseTestCase


class BaseOptimizationStrategyTest(InMemoryDatabaseTestCase):
    """Base test class for optimization strategy tests.

    Provides common fixtures and helper methods for testing different
    optimization strategies.

    Subclasses must override:
    - algorithm_name: The name of the algorithm to test (e.g., "greedy", "balanced")
    """

    # Override in subclasses
    algorithm_name = None

    @classmethod
    def setUpClass(cls):
        """Skip test execution for the base class itself and create in-memory DB."""
        if cls is BaseOptimizationStrategyTest:
            raise unittest.SkipTest("Skipping base test class")
        # Call parent to create in-memory database
        super().setUpClass()

    def setUp(self):
        """Clear database and initialize use cases for each test."""
        # Call parent to clear database
        super().setUp()
        # Initialize use cases
        self.create_use_case = CreateTaskUseCase(self.repository)
        config = ConfigManager.load()
        self.optimize_use_case = OptimizeScheduleUseCase(
            self.repository,
            config.time.default_start_hour,
            config.time.default_end_hour,
        )

    def create_task(
        self,
        name: str,
        priority: int = 100,
        estimated_duration: float = 10.0,
        deadline: datetime | None = None,
        is_fixed: bool = False,
    ) -> Task:
        """Helper to create a task and return the created task object.

        Args:
            name: Task name
            priority: Task priority (default: 100)
            estimated_duration: Duration in hours (default: 10.0)
            deadline: Optional deadline
            is_fixed: Whether the task is fixed (default: False)

        Returns:
            The created Task object
        """
        input_dto = CreateTaskInput(
            name=name,
            priority=priority,
            estimated_duration=estimated_duration,
            deadline=deadline,
            is_fixed=is_fixed,
        )
        result = self.create_use_case.execute(input_dto)
        # Return the actual Task entity from repository for test manipulation
        return self.repository.get_by_id(result.id)  # type: ignore[return-value]

    def optimize_schedule(
        self,
        start_date: datetime,
        max_hours_per_day: float = 6.0,
        force_override: bool = False,
    ):
        """Helper to run optimization with the algorithm being tested.

        Args:
            start_date: Start date for optimization
            max_hours_per_day: Maximum hours per day (default: 6.0)
            force_override: Whether to force override existing schedules (default: False)

        Returns:
            OptimizationOutput from the use case
        """
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            algorithm_name=self.algorithm_name,
            force_override=force_override,
        )
        return self.optimize_use_case.execute(optimize_input)

    def assert_task_scheduled(
        self,
        task: Task,
        expected_start: datetime | None = None,
        expected_end: datetime | None = None,
    ):
        """Assert that a task has been scheduled.

        Args:
            task: The task to check (will be re-fetched from repository to get updated state)
            expected_start: Optional expected start date/time
            expected_end: Optional expected end date/time
        """
        # Re-fetch task from repository to get updated state after optimization
        assert task.id is not None, "Task must have an ID"
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None, f"Task {task.id} not found in repository"

        self.assertIsNotNone(
            updated_task.planned_start,
            f"Task {updated_task.name} should have planned_start",
        )
        self.assertIsNotNone(
            updated_task.planned_end,
            f"Task {updated_task.name} should have planned_end",
        )
        self.assertIsNotNone(
            updated_task.daily_allocations,
            f"Task {updated_task.name} should have daily_allocations",
        )

        if expected_start:
            self.assertEqual(updated_task.planned_start, expected_start)
        if expected_end:
            self.assertEqual(updated_task.planned_end, expected_end)

    def assert_total_allocated_hours(
        self, task: Task, expected_hours: float, places: int = 5
    ):
        """Assert that the total allocated hours match expected.

        Args:
            task: The task to check (will be re-fetched from repository to get updated state)
            expected_hours: Expected total hours
            places: Decimal places for comparison (default: 5)
        """
        # Re-fetch task from repository to get updated state after optimization
        assert task.id is not None, "Task must have an ID"
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None, f"Task {task.id} not found in repository"

        self.assertIsNotNone(updated_task.daily_allocations)
        total = sum(updated_task.daily_allocations.values())
        self.assertAlmostEqual(
            total,
            expected_hours,
            places=places,
            msg=f"Total allocated hours for {updated_task.name}",
        )
