"""Tests for statistics converter functions."""

import pytest

from taskdog.infrastructure.api.converters.statistics_converters import (
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
            "total_logged_hours": 100.5,
            "average_task_duration": 5.0,
        }

        result = _parse_time_statistics(data)

        assert result.total_work_hours == 100.5
        assert result.average_work_hours == 5.0
        assert result.median_work_hours == 0.0  # Not available

    def test_missing_average(self):
        """Test with missing average_task_duration."""
        data = {
            "total_logged_hours": 50.0,
            "average_task_duration": None,
        }

        result = _parse_time_statistics(data)

        assert result.total_work_hours == 50.0
        assert result.average_work_hours == 0.0

    def test_zero_hours(self):
        """Test with zero logged hours."""
        data = {
            "total_logged_hours": 0.0,
            "average_task_duration": 0.0,
        }

        result = _parse_time_statistics(data)

        assert result.total_work_hours == 0.0
        assert result.average_work_hours == 0.0


class TestParseEstimationStatistics:
    """Test cases for _parse_estimation_statistics."""

    def test_basic_conversion(self):
        """Test basic estimation statistics conversion."""
        data = {
            "tasks_with_estimates": 50,
            "average_deviation_percentage": 15.5,
        }

        result = _parse_estimation_statistics(data)

        assert result.total_tasks_with_estimation == 50
        assert result.accuracy_rate == pytest.approx(0.155)
        # Default values for unavailable fields
        assert result.over_estimated_count == 0
        assert result.under_estimated_count == 0
        assert result.exact_count == 0

    def test_high_deviation(self):
        """Test with high deviation percentage."""
        data = {
            "tasks_with_estimates": 100,
            "average_deviation_percentage": 50.0,
        }

        result = _parse_estimation_statistics(data)

        assert result.accuracy_rate == pytest.approx(0.5)


class TestParseDeadlineStatistics:
    """Test cases for _parse_deadline_statistics."""

    @pytest.mark.parametrize(
        "met,missed,adherence_rate,expected_total,expected_compliance",
        [
            (80, 20, 0.8, 100, 0.8),
            (50, 0, 1.0, 50, 1.0),
            (0, 30, 0.0, 30, 0.0),
        ],
        ids=["basic", "all_met", "all_missed"],
    )
    def test_deadline_statistics(
        self, met, missed, adherence_rate, expected_total, expected_compliance
    ):
        """Test deadline statistics conversion."""
        data = {
            "met": met,
            "missed": missed,
            "adherence_rate": adherence_rate,
        }

        result = _parse_deadline_statistics(data)

        assert result.total_tasks_with_deadline == expected_total
        assert result.met_deadline_count == met
        assert result.missed_deadline_count == missed
        assert result.compliance_rate == expected_compliance
        assert result.average_delay_days == 0.0  # Not available


class TestParsePriorityStatistics:
    """Test cases for _parse_priority_statistics."""

    def test_basic_conversion(self):
        """Test basic priority statistics conversion."""
        data = {
            "distribution": {
                "80": 10,  # High
                "75": 15,  # High
                "50": 30,  # Medium
                "40": 20,  # Medium
                "25": 15,  # Low
                "10": 10,  # Low
            }
        }

        result = _parse_priority_statistics(data)

        assert result.high_priority_count == 25  # 80 + 75
        assert result.medium_priority_count == 50  # 50 + 40
        assert result.low_priority_count == 25  # 25 + 10
        assert len(result.priority_completion_map) == 6

    def test_only_high_priority(self):
        """Test with only high priority tasks."""
        data = {"distribution": {"90": 50, "80": 30, "70": 20}}

        result = _parse_priority_statistics(data)

        assert result.high_priority_count == 100
        assert result.medium_priority_count == 0
        assert result.low_priority_count == 0

    def test_boundary_values(self):
        """Test boundary values for priority categories."""
        data = {
            "distribution": {
                "70": 10,  # High (>= 70)
                "69": 5,  # Medium
                "30": 5,  # Medium (>= 30 and < 70)
                "29": 5,  # Low (< 30)
            }
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
            "completed_per_day": {
                "2025-01-01": 3,
                "2025-01-02": 5,
                "2025-01-03": 2,
                "2025-01-04": 4,
                "2025-01-05": 6,
                "2025-01-06": 1,
                "2025-01-07": 3,
            }
        }

        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == 24  # Sum of all
        assert result.last_30_days_completed == 24  # Same as above

    def test_more_than_7_days(self):
        """Test with more than 7 days of data."""
        completed = {f"2025-01-{i:02d}": 1 for i in range(1, 15)}
        data = {"completed_per_day": completed}

        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == 7  # Last 7 values
        assert result.last_30_days_completed == 14  # All 14 values

    def test_empty_data(self):
        """Test with empty completed_per_day."""
        data = {"completed_per_day": {}}

        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == 0
        assert result.last_30_days_completed == 0

    def test_missing_completed_per_day(self):
        """Test with missing completed_per_day field."""
        data = {}

        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == 0
        assert result.last_30_days_completed == 0


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
                "total_logged_hours": 500.0,
                "average_task_duration": 5.0,
            },
            "estimation": {
                "tasks_with_estimates": 50,
                "average_deviation_percentage": 10.0,
            },
            "deadline": {
                "met": 40,
                "missed": 10,
                "adherence_rate": 0.8,
            },
            "priority": {
                "distribution": {"80": 30, "50": 50, "20": 20},
            },
            "trends": {
                "completed_per_day": {"2025-01-01": 5, "2025-01-02": 3},
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
                "total_logged_hours": 200.0,
                "average_task_duration": 4.0,
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
