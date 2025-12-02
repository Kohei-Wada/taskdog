"""Test cases for CalculateStatisticsUseCase."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from taskdog_core.application.dto.statistics_output import CalculateStatisticsInput
from taskdog_core.application.use_cases.calculate_statistics import (
    CalculateStatisticsUseCase,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestCalculateStatisticsUseCase:
    """Test cases for CalculateStatisticsUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.repository = Mock()
        self.use_case = CalculateStatisticsUseCase(self.repository)

    def test_execute_with_empty_tasks(self):
        """Test execute with empty task list."""
        self.repository.get_all.return_value = []

        result = self.use_case.execute(CalculateStatisticsInput())

        assert result.task_stats.total_tasks == 0
        self.repository.get_all.assert_called_once()

    def test_execute_with_basic_tasks(self):
        """Test execute with basic tasks."""
        tasks = [
            Task(name="Task 1", priority=10, id=1, status=TaskStatus.PENDING),
            Task(name="Task 2", priority=20, id=2, status=TaskStatus.COMPLETED),
        ]
        self.repository.get_all.return_value = tasks

        result = self.use_case.execute(CalculateStatisticsInput())

        assert result.task_stats.total_tasks == 2
        assert result.task_stats.pending_count == 1
        assert result.task_stats.completed_count == 1
        self.repository.get_all.assert_called_once()

    def test_execute_with_period_filter(self):
        """Test execute with period filter."""
        now = datetime.now()
        tasks = [
            Task(
                name="Recent",
                priority=10,
                id=1,
                actual_end=(now - timedelta(days=3)),
                status=TaskStatus.COMPLETED,
            ),
            Task(
                name="Old",
                priority=20,
                id=2,
                actual_end=(now - timedelta(days=10)),
                status=TaskStatus.COMPLETED,
            ),
        ]
        self.repository.get_all.return_value = tasks

        result = self.use_case.execute(CalculateStatisticsInput(period="7d"))

        # Only the recent task should be counted
        assert result.task_stats.total_tasks == 1
        assert result.task_stats.completed_count == 1
        self.repository.get_all.assert_called_once()

    def test_execute_calculates_all_statistics(self):
        """Test that execute calculates all statistics sections."""
        now = datetime.now()
        tasks = [
            Task(
                name="Task 1",
                priority=100,
                id=1,
                status=TaskStatus.COMPLETED,
                estimated_duration=5.0,
                deadline=(now + timedelta(days=1)),
                actual_start=(now - timedelta(hours=3)),
                actual_end=now,
            ),
        ]
        self.repository.get_all.return_value = tasks

        result = self.use_case.execute(CalculateStatisticsInput())

        # Verify all statistics sections are calculated
        assert result.task_stats is not None
        assert result.time_stats is not None
        assert result.estimation_stats is not None
        assert result.deadline_stats is not None
        assert result.priority_stats is not None
        assert result.trend_stats is not None
