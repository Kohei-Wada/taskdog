"""Tests for statistics mapper."""

import unittest

from taskdog.mappers.statistics_mapper import StatisticsMapper
from taskdog.view_models.statistics_view_model import (
    EstimationAccuracyStatisticsViewModel,
    StatisticsViewModel,
    TaskSummaryViewModel,
    TimeStatisticsViewModel,
)
from taskdog_core.application.dto.statistics_output import (
    DeadlineComplianceStatistics,
    EstimationAccuracyStatistics,
    PriorityDistributionStatistics,
    StatisticsOutput,
    TaskStatistics,
    TimeStatistics,
    TrendStatistics,
)
from taskdog_core.application.dto.task_dto import TaskSummaryDto


class TestStatisticsMapper(unittest.TestCase):
    """Test cases for StatisticsMapper."""

    def _create_task_statistics(self) -> TaskStatistics:
        """Create a minimal TaskStatistics for tests."""
        return TaskStatistics(
            total_tasks=10,
            pending_count=3,
            in_progress_count=2,
            completed_count=4,
            canceled_count=1,
            completion_rate=0.4,
        )

    def _create_priority_statistics(self) -> PriorityDistributionStatistics:
        """Create a minimal PriorityDistributionStatistics for tests."""
        return PriorityDistributionStatistics(
            high_priority_count=2,
            medium_priority_count=5,
            low_priority_count=3,
            high_priority_completion_rate=0.5,
            priority_completion_map={50: 3, 80: 1},
        )

    def test_from_statistics_result_basic(self):
        """Test basic conversion without optional stats."""
        # Setup
        task_stats = self._create_task_statistics()
        priority_stats = self._create_priority_statistics()

        statistics_output = StatisticsOutput(
            task_stats=task_stats,
            priority_stats=priority_stats,
            time_stats=None,
            estimation_stats=None,
            deadline_stats=None,
            trend_stats=None,
        )

        # Execute
        result = StatisticsMapper.from_statistics_result(statistics_output)

        # Verify
        self.assertIsInstance(result, StatisticsViewModel)
        self.assertEqual(result.task_stats, task_stats)
        self.assertEqual(result.priority_stats, priority_stats)
        self.assertIsNone(result.time_stats)
        self.assertIsNone(result.estimation_stats)
        self.assertIsNone(result.deadline_stats)
        self.assertIsNone(result.trend_stats)

    def test_from_statistics_result_with_time_stats(self):
        """Test conversion with time statistics."""
        # Setup
        task_stats = self._create_task_statistics()
        priority_stats = self._create_priority_statistics()

        longest_task = TaskSummaryDto(id=1, name="Long Task")
        shortest_task = TaskSummaryDto(id=2, name="Short Task")

        time_stats = TimeStatistics(
            total_work_hours=100.0,
            average_work_hours=10.0,
            median_work_hours=8.0,
            longest_task=longest_task,
            shortest_task=shortest_task,
            tasks_with_time_tracking=10,
        )

        statistics_output = StatisticsOutput(
            task_stats=task_stats,
            priority_stats=priority_stats,
            time_stats=time_stats,
            estimation_stats=None,
            deadline_stats=None,
            trend_stats=None,
        )

        # Execute
        result = StatisticsMapper.from_statistics_result(statistics_output)

        # Verify
        self.assertIsNotNone(result.time_stats)
        self.assertIsInstance(result.time_stats, TimeStatisticsViewModel)
        self.assertEqual(result.time_stats.total_work_hours, 100.0)
        self.assertEqual(result.time_stats.average_work_hours, 10.0)
        self.assertEqual(result.time_stats.median_work_hours, 8.0)
        self.assertEqual(result.time_stats.tasks_with_time_tracking, 10)
        self.assertIsNotNone(result.time_stats.longest_task)
        self.assertEqual(result.time_stats.longest_task.id, 1)
        self.assertEqual(result.time_stats.longest_task.name, "Long Task")
        self.assertIsNotNone(result.time_stats.shortest_task)
        self.assertEqual(result.time_stats.shortest_task.id, 2)

    def test_from_statistics_result_with_time_stats_no_tasks(self):
        """Test conversion with time stats but no longest/shortest tasks."""
        # Setup
        task_stats = self._create_task_statistics()
        priority_stats = self._create_priority_statistics()

        time_stats = TimeStatistics(
            total_work_hours=50.0,
            average_work_hours=5.0,
            median_work_hours=4.0,
            longest_task=None,
            shortest_task=None,
            tasks_with_time_tracking=5,
        )

        statistics_output = StatisticsOutput(
            task_stats=task_stats,
            priority_stats=priority_stats,
            time_stats=time_stats,
            estimation_stats=None,
            deadline_stats=None,
            trend_stats=None,
        )

        # Execute
        result = StatisticsMapper.from_statistics_result(statistics_output)

        # Verify
        self.assertIsNotNone(result.time_stats)
        self.assertIsNone(result.time_stats.longest_task)
        self.assertIsNone(result.time_stats.shortest_task)

    def test_from_statistics_result_with_estimation_stats(self):
        """Test conversion with estimation statistics."""
        # Setup
        task_stats = self._create_task_statistics()
        priority_stats = self._create_priority_statistics()

        best_task = TaskSummaryDto(id=3, name="Best Estimated")
        worst_task = TaskSummaryDto(id=4, name="Worst Estimated")

        estimation_stats = EstimationAccuracyStatistics(
            total_tasks_with_estimation=8,
            accuracy_rate=0.95,
            over_estimated_count=2,
            under_estimated_count=1,
            exact_count=5,
            best_estimated_tasks=[best_task],
            worst_estimated_tasks=[worst_task],
        )

        statistics_output = StatisticsOutput(
            task_stats=task_stats,
            priority_stats=priority_stats,
            time_stats=None,
            estimation_stats=estimation_stats,
            deadline_stats=None,
            trend_stats=None,
        )

        # Execute
        result = StatisticsMapper.from_statistics_result(statistics_output)

        # Verify
        self.assertIsNotNone(result.estimation_stats)
        self.assertIsInstance(
            result.estimation_stats, EstimationAccuracyStatisticsViewModel
        )
        self.assertEqual(result.estimation_stats.total_tasks_with_estimation, 8)
        self.assertEqual(result.estimation_stats.accuracy_rate, 0.95)
        self.assertEqual(result.estimation_stats.over_estimated_count, 2)
        self.assertEqual(result.estimation_stats.under_estimated_count, 1)
        self.assertEqual(result.estimation_stats.exact_count, 5)
        self.assertEqual(len(result.estimation_stats.best_estimated_tasks), 1)
        self.assertEqual(result.estimation_stats.best_estimated_tasks[0].id, 3)
        self.assertEqual(len(result.estimation_stats.worst_estimated_tasks), 1)
        self.assertEqual(result.estimation_stats.worst_estimated_tasks[0].id, 4)

    def test_from_statistics_result_with_deadline_stats(self):
        """Test conversion with deadline statistics (pass-through)."""
        # Setup
        task_stats = self._create_task_statistics()
        priority_stats = self._create_priority_statistics()

        deadline_stats = DeadlineComplianceStatistics(
            total_tasks_with_deadline=5,
            met_deadline_count=4,
            missed_deadline_count=1,
            compliance_rate=0.8,
            average_delay_days=2.0,
        )

        statistics_output = StatisticsOutput(
            task_stats=task_stats,
            priority_stats=priority_stats,
            time_stats=None,
            estimation_stats=None,
            deadline_stats=deadline_stats,
            trend_stats=None,
        )

        # Execute
        result = StatisticsMapper.from_statistics_result(statistics_output)

        # Verify - deadline_stats is passed through directly
        self.assertEqual(result.deadline_stats, deadline_stats)

    def test_from_statistics_result_with_trend_stats(self):
        """Test conversion with trend statistics (pass-through)."""
        # Setup
        task_stats = self._create_task_statistics()
        priority_stats = self._create_priority_statistics()

        trend_stats = TrendStatistics(
            last_7_days_completed=3,
            last_30_days_completed=12,
            weekly_completion_trend={},
            monthly_completion_trend={"2025-01": 5, "2025-02": 7},
        )

        statistics_output = StatisticsOutput(
            task_stats=task_stats,
            priority_stats=priority_stats,
            time_stats=None,
            estimation_stats=None,
            deadline_stats=None,
            trend_stats=trend_stats,
        )

        # Execute
        result = StatisticsMapper.from_statistics_result(statistics_output)

        # Verify - trend_stats is passed through directly
        self.assertEqual(result.trend_stats, trend_stats)

    def test_from_statistics_result_complete(self):
        """Test conversion with all statistics present."""
        # Setup
        task_stats = self._create_task_statistics()
        priority_stats = self._create_priority_statistics()

        time_stats = TimeStatistics(
            total_work_hours=100.0,
            average_work_hours=10.0,
            median_work_hours=8.0,
            longest_task=TaskSummaryDto(id=1, name="Long Task"),
            shortest_task=TaskSummaryDto(id=2, name="Short Task"),
            tasks_with_time_tracking=10,
        )

        estimation_stats = EstimationAccuracyStatistics(
            total_tasks_with_estimation=8,
            accuracy_rate=0.95,
            over_estimated_count=2,
            under_estimated_count=1,
            exact_count=5,
            best_estimated_tasks=[],
            worst_estimated_tasks=[],
        )

        deadline_stats = DeadlineComplianceStatistics(
            total_tasks_with_deadline=5,
            met_deadline_count=4,
            missed_deadline_count=1,
            compliance_rate=0.8,
            average_delay_days=2.0,
        )

        trend_stats = TrendStatistics(
            last_7_days_completed=3,
            last_30_days_completed=12,
            weekly_completion_trend={},
            monthly_completion_trend={},
        )

        statistics_output = StatisticsOutput(
            task_stats=task_stats,
            priority_stats=priority_stats,
            time_stats=time_stats,
            estimation_stats=estimation_stats,
            deadline_stats=deadline_stats,
            trend_stats=trend_stats,
        )

        # Execute
        result = StatisticsMapper.from_statistics_result(statistics_output)

        # Verify all stats are present
        self.assertIsNotNone(result.task_stats)
        self.assertIsNotNone(result.priority_stats)
        self.assertIsNotNone(result.time_stats)
        self.assertIsNotNone(result.estimation_stats)
        self.assertIsNotNone(result.deadline_stats)
        self.assertIsNotNone(result.trend_stats)


class TestMapTaskToSummary(unittest.TestCase):
    """Test cases for _map_task_to_summary method."""

    def test_map_task_to_summary(self):
        """Test mapping TaskSummaryDto to TaskSummaryViewModel."""
        # Setup
        task_dto = TaskSummaryDto(id=42, name="Test Task")

        # Execute
        result = StatisticsMapper._map_task_to_summary(task_dto)

        # Verify
        self.assertIsInstance(result, TaskSummaryViewModel)
        self.assertEqual(result.id, 42)
        self.assertEqual(result.name, "Test Task")
        self.assertIsNone(result.estimated_duration)
        self.assertIsNone(result.actual_duration_hours)


if __name__ == "__main__":
    unittest.main()
