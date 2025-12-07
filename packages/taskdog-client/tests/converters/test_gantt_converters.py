"""Tests for Gantt converter functions."""

from datetime import date, datetime

import pytest
from taskdog_client.converters.gantt_converters import (
    convert_to_gantt_output,
)

from taskdog_core.domain.entities.task import TaskStatus


class TestConvertToGanttOutput:
    """Test cases for convert_to_gantt_output."""

    def test_complete_data(self):
        """Test conversion with complete data."""
        data = {
            "date_range": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "status": "PENDING",
                    "estimated_duration": 5.0,
                    "planned_start": "2025-01-05T09:00:00",
                    "planned_end": "2025-01-10T17:00:00",
                    "actual_start": None,
                    "actual_end": None,
                    "deadline": "2025-01-15T23:59:00",
                }
            ],
            "task_daily_hours": {
                "1": {
                    "2025-01-05": 2.0,
                    "2025-01-06": 3.0,
                }
            },
            "daily_workload": {
                "2025-01-05": 2.0,
                "2025-01-06": 3.0,
            },
            "holidays": ["2025-01-01", "2025-01-13"],
            "total_estimated_duration": 5.0,
        }

        result = convert_to_gantt_output(data)

        assert result.date_range.start_date == date(2025, 1, 1)
        assert result.date_range.end_date == date(2025, 1, 31)
        assert len(result.tasks) == 1
        assert result.tasks[0].id == 1
        assert result.tasks[0].name == "Task 1"
        assert result.tasks[0].status == TaskStatus.PENDING
        assert result.tasks[0].estimated_duration == 5.0
        assert result.tasks[0].planned_start == datetime(2025, 1, 5, 9, 0, 0)
        assert len(result.holidays) == 2
        assert date(2025, 1, 1) in result.holidays
        assert result.total_estimated_duration == 5.0

    def test_date_range_conversion(self):
        """Test that date_range dates are converted correctly."""
        data = {
            "date_range": {
                "start_date": "2025-06-01",
                "end_date": "2025-06-30",
            },
            "tasks": [],
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_output(data)

        assert result.date_range.start_date == date(2025, 6, 1)
        assert result.date_range.end_date == date(2025, 6, 30)

    @pytest.mark.parametrize(
        "status_str,expected_status,expected_finished",
        [
            ("pending", TaskStatus.PENDING, False),
            ("in_progress", TaskStatus.IN_PROGRESS, False),
            ("completed", TaskStatus.COMPLETED, True),
            ("CANCELED", TaskStatus.CANCELED, True),
        ],
        ids=["pending", "in_progress", "completed", "canceled"],
    )
    def test_task_status_conversion(
        self, status_str, expected_status, expected_finished
    ):
        """Test that task statuses are converted correctly."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [
                {
                    "id": 1,
                    "name": "Task",
                    "status": status_str,
                    "estimated_duration": None,
                    "planned_start": None,
                    "planned_end": None,
                    "actual_start": "2025-01-10T09:00:00"
                    if status_str != "pending"
                    else None,
                    "actual_end": "2025-01-15T17:00:00"
                    if status_str in ("completed", "CANCELED")
                    else None,
                    "deadline": None,
                }
            ],
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_output(data)

        assert result.tasks[0].status == expected_status
        assert result.tasks[0].is_finished == expected_finished

    def test_task_daily_hours_conversion(self):
        """Test that task_daily_hours are converted correctly."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [],
            "task_daily_hours": {
                "1": {"2025-01-05": 2.0, "2025-01-06": 3.0},
                "2": {"2025-01-05": 1.0},
            },
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_output(data)

        assert len(result.task_daily_hours) == 2
        assert result.task_daily_hours[1][date(2025, 1, 5)] == 2.0
        assert result.task_daily_hours[1][date(2025, 1, 6)] == 3.0
        assert result.task_daily_hours[2][date(2025, 1, 5)] == 1.0

    def test_daily_workload_conversion(self):
        """Test that daily_workload is converted correctly."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [],
            "task_daily_hours": {},
            "daily_workload": {
                "2025-01-05": 4.0,
                "2025-01-06": 6.0,
                "2025-01-07": 8.0,
            },
            "holidays": [],
        }

        result = convert_to_gantt_output(data)

        assert len(result.daily_workload) == 3
        assert result.daily_workload[date(2025, 1, 5)] == 4.0
        assert result.daily_workload[date(2025, 1, 6)] == 6.0
        assert result.daily_workload[date(2025, 1, 7)] == 8.0

    def test_holidays_conversion(self):
        """Test that holidays are converted correctly."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [],
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": ["2025-01-01", "2025-01-13", "2025-12-25"],
        }

        result = convert_to_gantt_output(data)

        assert len(result.holidays) == 3
        assert date(2025, 1, 1) in result.holidays
        assert date(2025, 1, 13) in result.holidays
        assert date(2025, 12, 25) in result.holidays

    def test_empty_holidays(self):
        """Test conversion with no holidays."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [],
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_output(data)

        assert len(result.holidays) == 0

    def test_default_total_estimated_duration(self):
        """Test that total_estimated_duration defaults to 0.0."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [],
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_output(data)

        assert result.total_estimated_duration == 0.0

    def test_multiple_tasks(self):
        """Test conversion with multiple tasks."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "status": "PENDING",
                    "estimated_duration": 5.0,
                    "planned_start": "2025-01-05T09:00:00",
                    "planned_end": "2025-01-10T17:00:00",
                    "actual_start": None,
                    "actual_end": None,
                    "deadline": None,
                },
                {
                    "id": 2,
                    "name": "Task 2",
                    "status": "IN_PROGRESS",
                    "estimated_duration": 3.0,
                    "planned_start": "2025-01-11T09:00:00",
                    "planned_end": "2025-01-14T17:00:00",
                    "actual_start": "2025-01-11T09:00:00",
                    "actual_end": None,
                    "deadline": "2025-01-20T23:59:00",
                },
            ],
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
            "total_estimated_duration": 8.0,
        }

        result = convert_to_gantt_output(data)

        assert len(result.tasks) == 2
        assert result.tasks[0].estimated_duration == 5.0
        assert result.tasks[1].estimated_duration == 3.0
        assert result.tasks[1].actual_start is not None
        assert result.tasks[1].deadline is not None
        assert result.total_estimated_duration == 8.0
