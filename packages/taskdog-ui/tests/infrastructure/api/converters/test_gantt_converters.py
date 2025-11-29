"""Tests for Gantt converter functions."""

import unittest
from datetime import date, datetime

from taskdog.infrastructure.api.converters.gantt_converters import (
    convert_to_gantt_output,
)
from taskdog_core.domain.entities.task import TaskStatus


class TestConvertToGanttOutput(unittest.TestCase):
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

        self.assertEqual(result.date_range.start_date, date(2025, 1, 1))
        self.assertEqual(result.date_range.end_date, date(2025, 1, 31))
        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].id, 1)
        self.assertEqual(result.tasks[0].name, "Task 1")
        self.assertEqual(result.tasks[0].status, TaskStatus.PENDING)
        self.assertEqual(result.tasks[0].estimated_duration, 5.0)
        self.assertEqual(result.tasks[0].planned_start, datetime(2025, 1, 5, 9, 0, 0))
        self.assertEqual(len(result.holidays), 2)
        self.assertIn(date(2025, 1, 1), result.holidays)
        self.assertEqual(result.total_estimated_duration, 5.0)

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

        self.assertEqual(result.date_range.start_date, date(2025, 6, 1))
        self.assertEqual(result.date_range.end_date, date(2025, 6, 30))

    def test_task_status_conversion(self):
        """Test that task statuses are converted correctly."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [
                {
                    "id": 1,
                    "name": "Pending",
                    "status": "pending",
                    "estimated_duration": None,
                    "planned_start": None,
                    "planned_end": None,
                    "actual_start": None,
                    "actual_end": None,
                    "deadline": None,
                },
                {
                    "id": 2,
                    "name": "In Progress",
                    "status": "in_progress",
                    "estimated_duration": None,
                    "planned_start": None,
                    "planned_end": None,
                    "actual_start": "2025-01-10T09:00:00",
                    "actual_end": None,
                    "deadline": None,
                },
                {
                    "id": 3,
                    "name": "Completed",
                    "status": "completed",
                    "estimated_duration": None,
                    "planned_start": None,
                    "planned_end": None,
                    "actual_start": "2025-01-01T09:00:00",
                    "actual_end": "2025-01-05T17:00:00",
                    "deadline": None,
                },
            ],
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_output(data)

        self.assertEqual(result.tasks[0].status, TaskStatus.PENDING)
        self.assertFalse(result.tasks[0].is_finished)
        self.assertEqual(result.tasks[1].status, TaskStatus.IN_PROGRESS)
        self.assertFalse(result.tasks[1].is_finished)
        self.assertEqual(result.tasks[2].status, TaskStatus.COMPLETED)
        self.assertTrue(result.tasks[2].is_finished)

    def test_canceled_task_is_finished(self):
        """Test that canceled tasks are marked as finished."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "tasks": [
                {
                    "id": 1,
                    "name": "Canceled",
                    "status": "CANCELED",
                    "estimated_duration": None,
                    "planned_start": None,
                    "planned_end": None,
                    "actual_start": None,
                    "actual_end": None,
                    "deadline": None,
                }
            ],
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_output(data)

        self.assertEqual(result.tasks[0].status, TaskStatus.CANCELED)
        self.assertTrue(result.tasks[0].is_finished)

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

        self.assertEqual(len(result.task_daily_hours), 2)
        self.assertEqual(result.task_daily_hours[1][date(2025, 1, 5)], 2.0)
        self.assertEqual(result.task_daily_hours[1][date(2025, 1, 6)], 3.0)
        self.assertEqual(result.task_daily_hours[2][date(2025, 1, 5)], 1.0)

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

        self.assertEqual(len(result.daily_workload), 3)
        self.assertEqual(result.daily_workload[date(2025, 1, 5)], 4.0)
        self.assertEqual(result.daily_workload[date(2025, 1, 6)], 6.0)
        self.assertEqual(result.daily_workload[date(2025, 1, 7)], 8.0)

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

        self.assertEqual(len(result.holidays), 3)
        self.assertIn(date(2025, 1, 1), result.holidays)
        self.assertIn(date(2025, 1, 13), result.holidays)
        self.assertIn(date(2025, 12, 25), result.holidays)

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

        self.assertEqual(len(result.holidays), 0)

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

        self.assertEqual(result.total_estimated_duration, 0.0)

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

        self.assertEqual(len(result.tasks), 2)
        self.assertEqual(result.tasks[0].estimated_duration, 5.0)
        self.assertEqual(result.tasks[1].estimated_duration, 3.0)
        self.assertIsNotNone(result.tasks[1].actual_start)
        self.assertIsNotNone(result.tasks[1].deadline)
        self.assertEqual(result.total_estimated_duration, 8.0)


if __name__ == "__main__":
    unittest.main()
