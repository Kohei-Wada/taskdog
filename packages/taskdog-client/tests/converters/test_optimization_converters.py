"""Tests for optimization converter functions."""

from taskdog_client.converters.optimization_converters import (
    _parse_optimization_summary,
    _parse_scheduling_failures,
    convert_to_optimization_output,
)


class TestParseOptimizationSummary:
    """Test cases for _parse_optimization_summary."""

    def test_basic_conversion(self):
        """Test basic summary conversion."""
        summary = {
            "scheduled_tasks": 8,
            "total_hours": 40.0,
            "start_date": "2025-01-01",
            "end_date": "2025-01-10",
        }
        failures = [
            {"task_id": 11, "task_name": "Failed Task 1", "reason": "No time"},
            {"task_id": 12, "task_name": "Failed Task 2", "reason": "Conflict"},
        ]

        result = _parse_optimization_summary(summary, failures)

        assert result.new_count == 8
        assert result.rescheduled_count == 0
        assert result.total_hours == 40.0
        assert result.days_span == 10  # 10 days inclusive
        assert len(result.unscheduled_tasks) == 2
        assert result.unscheduled_tasks[0].id == 11
        assert result.unscheduled_tasks[1].id == 12

    def test_single_day_span(self):
        """Test calculation with single day."""
        summary = {
            "scheduled_tasks": 2,
            "total_hours": 8.0,
            "start_date": "2025-01-15",
            "end_date": "2025-01-15",
        }
        failures = []

        result = _parse_optimization_summary(summary, failures)

        assert result.days_span == 1

    def test_no_failures(self):
        """Test with no scheduling failures."""
        summary = {
            "scheduled_tasks": 10,
            "total_hours": 50.0,
            "start_date": "2025-01-01",
            "end_date": "2025-01-07",
        }
        failures = []

        result = _parse_optimization_summary(summary, failures)

        assert result.new_count == 10
        assert len(result.unscheduled_tasks) == 0

    def test_all_failed(self):
        """Test when all tasks fail to schedule."""
        summary = {
            "scheduled_tasks": 0,
            "total_hours": 0.0,
            "start_date": "2025-01-01",
            "end_date": "2025-01-05",
        }
        failures = [
            {"task_id": 1, "task_name": "Task 1", "reason": "No time slot"},
            {"task_id": 2, "task_name": "Task 2", "reason": "Dependencies"},
            {"task_id": 3, "task_name": "Task 3", "reason": "Past deadline"},
        ]

        result = _parse_optimization_summary(summary, failures)

        assert result.new_count == 0
        assert len(result.unscheduled_tasks) == 3


class TestParseSchedulingFailures:
    """Test cases for _parse_scheduling_failures."""

    def test_multiple_failures(self):
        """Test parsing multiple failures."""
        failures = [
            {"task_id": 1, "task_name": "Task 1", "reason": "No available time slot"},
            {"task_id": 2, "task_name": "Task 2", "reason": "Dependency not met"},
            {"task_id": 3, "task_name": "Task 3", "reason": "Deadline passed"},
        ]

        result = _parse_scheduling_failures(failures)

        assert len(result) == 3
        assert result[0].task.id == 1
        assert result[0].task.name == "Task 1"
        assert result[0].reason == "No available time slot"
        assert result[1].task.id == 2
        assert result[2].reason == "Deadline passed"

    def test_empty_failures(self):
        """Test parsing empty failures list."""
        failures = []

        result = _parse_scheduling_failures(failures)

        assert result == []

    def test_single_failure(self):
        """Test parsing single failure."""
        failures = [
            {"task_id": 42, "task_name": "Important Task", "reason": "Conflict"},
        ]

        result = _parse_scheduling_failures(failures)

        assert len(result) == 1
        assert result[0].task.id == 42
        assert result[0].task.name == "Important Task"
        assert result[0].reason == "Conflict"


class TestConvertToOptimizationOutput:
    """Test cases for convert_to_optimization_output."""

    def test_complete_data(self):
        """Test conversion with complete data."""
        data = {
            "summary": {
                "total_tasks": 10,
                "scheduled_tasks": 8,
                "failed_tasks": 2,
                "total_hours": 40.0,
                "start_date": "2025-01-01",
                "end_date": "2025-01-10",
                "algorithm": "greedy",
            },
            "failures": [
                {"task_id": 11, "task_name": "Task 11", "reason": "No available time"},
                {
                    "task_id": 12,
                    "task_name": "Task 12",
                    "reason": "Dependency conflict",
                },
            ],
            "message": "Optimization completed",
        }

        result = convert_to_optimization_output(data)

        assert result.summary.new_count == 8
        assert result.summary.total_hours == 40.0
        assert result.summary.days_span == 10
        assert len(result.failed_tasks) == 2
        assert result.failed_tasks[0].task.id == 11
        assert result.failed_tasks[0].reason == "No available time"
        assert len(result.successful_tasks) == 8

    def test_all_successful(self):
        """Test when all tasks are scheduled successfully."""
        data = {
            "summary": {
                "total_tasks": 5,
                "scheduled_tasks": 5,
                "failed_tasks": 0,
                "total_hours": 25.0,
                "start_date": "2025-01-01",
                "end_date": "2025-01-05",
                "algorithm": "balanced",
            },
            "failures": [],
            "message": "All tasks scheduled",
        }

        result = convert_to_optimization_output(data)

        assert result.summary.new_count == 5
        assert len(result.failed_tasks) == 0
        assert len(result.successful_tasks) == 5
        assert len(result.summary.unscheduled_tasks) == 0

    def test_all_failed(self):
        """Test when all tasks fail to schedule."""
        data = {
            "summary": {
                "total_tasks": 3,
                "scheduled_tasks": 0,
                "failed_tasks": 3,
                "total_hours": 0.0,
                "start_date": "2025-01-01",
                "end_date": "2025-01-01",
                "algorithm": "greedy",
            },
            "failures": [
                {"task_id": 1, "task_name": "Task 1", "reason": "Error 1"},
                {"task_id": 2, "task_name": "Task 2", "reason": "Error 2"},
                {"task_id": 3, "task_name": "Task 3", "reason": "Error 3"},
            ],
            "message": "All tasks failed",
        }

        result = convert_to_optimization_output(data)

        assert result.summary.new_count == 0
        assert len(result.failed_tasks) == 3
        assert len(result.successful_tasks) == 0
        assert len(result.summary.unscheduled_tasks) == 3

    def test_daily_allocations_empty(self):
        """Test that daily_allocations is empty (not provided by API)."""
        data = {
            "summary": {
                "total_tasks": 5,
                "scheduled_tasks": 5,
                "failed_tasks": 0,
                "total_hours": 25.0,
                "start_date": "2025-01-01",
                "end_date": "2025-01-05",
                "algorithm": "greedy",
            },
            "failures": [],
            "message": "Success",
        }

        result = convert_to_optimization_output(data)

        assert result.daily_allocations == {}

    def test_task_states_before_empty(self):
        """Test that task_states_before is empty (not provided by API)."""
        data = {
            "summary": {
                "total_tasks": 5,
                "scheduled_tasks": 5,
                "failed_tasks": 0,
                "total_hours": 25.0,
                "start_date": "2025-01-01",
                "end_date": "2025-01-05",
                "algorithm": "greedy",
            },
            "failures": [],
            "message": "Success",
        }

        result = convert_to_optimization_output(data)

        assert result.task_states_before == {}
