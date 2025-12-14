"""Tests for statistics converter functions."""

import pytest
from taskdog_client.converters.statistics_converters import (
    _parse_deadline_statistics,
    _parse_estimation_statistics,
    _parse_priority_statistics,
    _parse_task_statistics,
    _parse_time_statistics,
    _parse_trend_statistics,
    convert_to_statistics_output,
)


class TestParseTaskStatistics:
    """Test cases for _parse_task_statistics."""

    def test_basic_conversion(self):
        """Test basic task statistics conversion."""
        data = {
            "total": 100,
            "pending": 20,
            "in_progress": 10,
            "completed": 60,
            "canceled": 10,
            "completion_rate": 0.6,
        }

        result = _parse_task_statistics(data)

        assert result.total_tasks == 100
        assert result.pending_count == 20
        assert result.in_progress_count == 10
        assert result.completed_count == 60
        assert result.canceled_count == 10
        assert result.completion_rate == 0.6

    def test_all_pending(self):
        """Test with all tasks pending."""
        data = {
            "total": 50,
            "pending": 50,
            "in_progress": 0,
            "completed": 0,
            "canceled": 0,
            "completion_rate": 0.0,
        }

        result = _parse_task_statistics(data)

        assert result.total_tasks == 50
        assert result.pending_count == 50
        assert result.completion_rate == 0.0

    def test_all_completed(self):
        """Test with all tasks completed."""
        data = {
            "total": 50,
            "pending": 0,
            "in_progress": 0,
            "completed": 50,
            "canceled": 0,
            "completion_rate": 1.0,
        }

        result = _parse_task_statistics(data)

        assert result.completed_count == 50
        assert result.completion_rate == 1.0


class TestParseTimeStatistics:
    """Test cases for _parse_time_statistics."""

    def test_basic_conversion(self):
        """Test basic time statistics conversion."""
        data = {
            "total_work_hours": 100.5,
            "average_work_hours": 5.0,
        }

        result = _parse_time_statistics(data)

        assert result.total_work_hours == 100.5
        assert result.average_work_hours == 5.0
        assert result.median_work_hours == 0.0  # Not available

    def test_missing_average(self):
        """Test with missing average_work_hours."""
        data = {
            "total_work_hours": 50.0,
            "average_work_hours": None,
        }

        result = _parse_time_statistics(data)

        assert result.total_work_hours == 50.0
        assert result.average_work_hours == 0.0

    def test_zero_hours(self):
        """Test with zero logged hours."""
        data = {
            "total_work_hours": 0.0,
            "average_work_hours": 0.0,
        }

        result = _parse_time_statistics(data)

        assert result.total_work_hours == 0.0
        assert result.average_work_hours == 0.0


class TestParseEstimationStatistics:
    """Test cases for _parse_estimation_statistics."""

    def test_basic_conversion(self):
        """Test basic estimation statistics conversion."""
        data = {
            "total_tasks_with_estimation": 50,
            "accuracy_rate": 0.95,
            "over_estimated_count": 10,
            "under_estimated_count": 5,
            "exact_count": 35,
            "best_estimated_tasks": [{"id": 1, "name": "Task 1"}],
            "worst_estimated_tasks": [{"id": 2, "name": "Task 2"}],
        }

        result = _parse_estimation_statistics(data)

        assert result.total_tasks_with_estimation == 50
        assert result.accuracy_rate == 0.95
        assert result.over_estimated_count == 10
        assert result.under_estimated_count == 5
        assert result.exact_count == 35
        assert len(result.best_estimated_tasks) == 1
        assert len(result.worst_estimated_tasks) == 1

    def test_high_deviation(self):
        """Test with high accuracy rate."""
        data = {
            "total_tasks_with_estimation": 100,
            "accuracy_rate": 1.5,  # 150% - over estimate
        }

        result = _parse_estimation_statistics(data)

        assert result.accuracy_rate == 1.5


class TestParseDeadlineStatistics:
    """Test cases for _parse_deadline_statistics."""

    @pytest.mark.parametrize(
        "met,missed,compliance_rate,expected_total",
        [
            (80, 20, 0.8, 100),
            (50, 0, 1.0, 50),
            (0, 30, 0.0, 30),
        ],
        ids=["basic", "all_met", "all_missed"],
    )
    def test_deadline_statistics(self, met, missed, compliance_rate, expected_total):
        """Test deadline statistics conversion."""
        data = {
            "total_tasks_with_deadline": expected_total,
            "met_deadline_count": met,
            "missed_deadline_count": missed,
            "compliance_rate": compliance_rate,
        }

        result = _parse_deadline_statistics(data)

        assert result.total_tasks_with_deadline == expected_total
        assert result.met_deadline_count == met
        assert result.missed_deadline_count == missed
        assert result.compliance_rate == compliance_rate
        assert result.average_delay_days == 0.0  # Not available


class TestParsePriorityStatistics:
    """Test cases for _parse_priority_statistics."""

    def test_basic_conversion(self):
        """Test basic priority statistics conversion."""
        data = {
            "distribution": {
                "80": 10,
                "75": 15,
                "50": 30,
                "40": 20,
                "25": 15,
                "10": 10,
            },
            "high_priority_count": 25,
            "medium_priority_count": 50,
            "low_priority_count": 25,
            "high_priority_completion_rate": 0.8,
        }

        result = _parse_priority_statistics(data)

        assert result.high_priority_count == 25
        assert result.medium_priority_count == 50
        assert result.low_priority_count == 25
        assert result.high_priority_completion_rate == 0.8
        assert len(result.priority_completion_map) == 6

    def test_only_high_priority(self):
        """Test with only high priority tasks."""
        data = {
            "distribution": {"90": 50, "80": 30, "70": 20},
            "high_priority_count": 100,
            "medium_priority_count": 0,
            "low_priority_count": 0,
        }

        result = _parse_priority_statistics(data)

        assert result.high_priority_count == 100
        assert result.medium_priority_count == 0
        assert result.low_priority_count == 0

    def test_boundary_values(self):
        """Test boundary values for priority categories."""
        data = {
            "distribution": {
                "70": 10,
                "69": 5,
                "30": 5,
                "29": 5,
            },
            "high_priority_count": 10,
            "medium_priority_count": 10,
            "low_priority_count": 5,
        }

        result = _parse_priority_statistics(data)

        assert result.high_priority_count == 10
        assert result.medium_priority_count == 10
        assert result.low_priority_count == 5


class TestParseTrendStatistics:
    """Test cases for _parse_trend_statistics."""

    def test_basic_conversion(self):
        """Test basic trend statistics conversion."""
        data = {
            "last_7_days_completed": 24,
            "last_30_days_completed": 45,
            "weekly_completion_trend": {"2025-W01": 24},
            "monthly_completion_trend": {"2025-01": 45},
        }

        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == 24
        assert result.last_30_days_completed == 45
        assert result.weekly_completion_trend == {"2025-W01": 24}
        assert result.monthly_completion_trend == {"2025-01": 45}

    def test_more_than_7_days(self):
        """Test with larger data."""
        data = {
            "last_7_days_completed": 7,
            "last_30_days_completed": 14,
            "weekly_completion_trend": {"2025-W01": 7, "2025-W02": 7},
            "monthly_completion_trend": {"2025-01": 14},
        }

        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == 7
        assert result.last_30_days_completed == 14

    def test_empty_data(self):
        """Test with empty trend data."""
        data = {
            "last_7_days_completed": 0,
            "last_30_days_completed": 0,
            "weekly_completion_trend": {},
            "monthly_completion_trend": {},
        }

        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == 0
        assert result.last_30_days_completed == 0

    def test_missing_fields(self):
        """Test with missing fields (defaults to 0 / empty)."""
        data = {}

        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == 0
        assert result.last_30_days_completed == 0
        assert result.weekly_completion_trend == {}
        assert result.monthly_completion_trend == {}


class TestConvertToStatisticsOutput:
    """Test cases for convert_to_statistics_output."""

    def test_complete_data(self):
        """Test conversion with all statistics sections."""
        data = {
            "completion": {
                "total": 100,
                "pending": 20,
                "in_progress": 10,
                "completed": 60,
                "canceled": 10,
                "completion_rate": 0.6,
            },
            "time": {
                "total_work_hours": 500.0,
                "average_work_hours": 5.0,
            },
            "estimation": {
                "total_tasks_with_estimation": 50,
                "accuracy_rate": 0.9,
            },
            "deadline": {
                "total_tasks_with_deadline": 50,
                "met_deadline_count": 40,
                "missed_deadline_count": 10,
                "compliance_rate": 0.8,
            },
            "priority": {
                "distribution": {"80": 30, "50": 50, "20": 20},
            },
            "trends": {
                "last_7_days_completed": 8,
                "last_30_days_completed": 60,
            },
        }

        result = convert_to_statistics_output(data)

        assert result.task_stats is not None
        assert result.task_stats.total_tasks == 100
        assert result.time_stats is not None
        assert result.time_stats.total_work_hours == 500.0
        assert result.estimation_stats is not None
        assert result.deadline_stats is not None
        assert result.priority_stats is not None
        assert result.trend_stats is not None

    def test_minimal_data(self):
        """Test conversion with only required sections."""
        data = {
            "completion": {
                "total": 50,
                "pending": 25,
                "in_progress": 5,
                "completed": 15,
                "canceled": 5,
                "completion_rate": 0.3,
            },
            "priority": {
                "distribution": {"50": 50},
            },
        }

        result = convert_to_statistics_output(data)

        assert result.task_stats is not None
        assert result.time_stats is None
        assert result.estimation_stats is None
        assert result.deadline_stats is None
        assert result.priority_stats is not None
        assert result.trend_stats is None

    def test_with_time_only(self):
        """Test conversion with time stats but no other optional sections."""
        data = {
            "completion": {
                "total": 100,
                "pending": 50,
                "in_progress": 10,
                "completed": 40,
                "canceled": 0,
                "completion_rate": 0.4,
            },
            "time": {
                "total_work_hours": 200.0,
                "average_work_hours": 4.0,
            },
            "priority": {
                "distribution": {"50": 100},
            },
        }

        result = convert_to_statistics_output(data)

        assert result.task_stats is not None
        assert result.time_stats is not None
        assert result.estimation_stats is None
        assert result.deadline_stats is None
        assert result.priority_stats is not None
        assert result.trend_stats is None
