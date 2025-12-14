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

    @pytest.mark.parametrize(
        "total,pending,in_progress,completed,canceled,rate",
        [
            (100, 20, 10, 60, 10, 0.6),
            (50, 50, 0, 0, 0, 0.0),
            (50, 0, 0, 50, 0, 1.0),
        ],
        ids=["basic", "all_pending", "all_completed"],
    )
    def test_parse_task_statistics(
        self, total, pending, in_progress, completed, canceled, rate
    ):
        """Test task statistics conversion with various scenarios."""
        data = {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "canceled": canceled,
            "completion_rate": rate,
        }

        result = _parse_task_statistics(data)

        assert result.total_tasks == total
        assert result.pending_count == pending
        assert result.in_progress_count == in_progress
        assert result.completed_count == completed
        assert result.canceled_count == canceled
        assert result.completion_rate == rate


class TestParseTimeStatistics:
    """Test cases for _parse_time_statistics."""

    @pytest.mark.parametrize(
        "total_hours,avg_hours,expected_avg",
        [
            (100.5, 5.0, 5.0),
            (50.0, None, 0.0),
            (0.0, 0.0, 0.0),
        ],
        ids=["basic", "missing_average", "zero_hours"],
    )
    def test_parse_time_statistics(self, total_hours, avg_hours, expected_avg):
        """Test time statistics conversion with various scenarios."""
        data = {
            "total_work_hours": total_hours,
            "average_work_hours": avg_hours,
        }

        result = _parse_time_statistics(data)

        assert result.total_work_hours == total_hours
        assert result.average_work_hours == expected_avg
        assert result.median_work_hours == 0.0  # Not available from API


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

    @pytest.mark.parametrize(
        "data,expected_7d,expected_30d,expected_weekly,expected_monthly",
        [
            (
                {
                    "last_7_days_completed": 24,
                    "last_30_days_completed": 45,
                    "weekly_completion_trend": {"2025-W01": 24},
                    "monthly_completion_trend": {"2025-01": 45},
                },
                24,
                45,
                {"2025-W01": 24},
                {"2025-01": 45},
            ),
            (
                {
                    "last_7_days_completed": 7,
                    "last_30_days_completed": 14,
                    "weekly_completion_trend": {"2025-W01": 7, "2025-W02": 7},
                    "monthly_completion_trend": {"2025-01": 14},
                },
                7,
                14,
                {"2025-W01": 7, "2025-W02": 7},
                {"2025-01": 14},
            ),
            (
                {
                    "last_7_days_completed": 0,
                    "last_30_days_completed": 0,
                    "weekly_completion_trend": {},
                    "monthly_completion_trend": {},
                },
                0,
                0,
                {},
                {},
            ),
            ({}, 0, 0, {}, {}),
        ],
        ids=["basic", "multiple_weeks", "empty_data", "missing_fields"],
    )
    def test_parse_trend_statistics(
        self, data, expected_7d, expected_30d, expected_weekly, expected_monthly
    ):
        """Test trend statistics conversion with various scenarios."""
        result = _parse_trend_statistics(data)

        assert result.last_7_days_completed == expected_7d
        assert result.last_30_days_completed == expected_30d
        assert result.weekly_completion_trend == expected_weekly
        assert result.monthly_completion_trend == expected_monthly


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
