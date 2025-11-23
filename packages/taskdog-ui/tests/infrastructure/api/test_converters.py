"""Tests for API response converters."""

import unittest
from datetime import datetime

from taskdog.infrastructure.api.converters import (
    ConversionError,
    convert_to_gantt_output,
    convert_to_get_task_by_id_output,
    convert_to_get_task_detail_output,
    convert_to_optimization_output,
    convert_to_statistics_output,
    convert_to_tag_statistics_output,
    convert_to_task_list_output,
    convert_to_task_operation_output,
    convert_to_update_task_output,
)
from taskdog_core.domain.entities.task import TaskStatus


class TestConverters(unittest.TestCase):
    """Test cases for API response converters."""

    def test_convert_to_task_operation_output(self):
        """Test convert_to_task_operation_output with complete data."""
        data = {
            "id": 1,
            "name": "Test Task",
            "status": "PENDING",
            "priority": 50,
            "deadline": "2025-12-31T23:59:00",
            "estimated_duration": 5.0,
            "planned_start": "2025-01-01T09:00:00",
            "planned_end": "2025-01-05T17:00:00",
            "actual_start": None,
            "actual_end": None,
            "depends_on": [2, 3],
            "tags": ["urgent", "backend"],
            "is_fixed": False,
            "is_archived": False,
            "actual_duration_hours": None,
            "actual_daily_hours": {},
        }

        result = convert_to_task_operation_output(data)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "Test Task")
        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertEqual(result.priority, 50)
        self.assertEqual(result.deadline, datetime(2025, 12, 31, 23, 59, 0))
        self.assertEqual(result.estimated_duration, 5.0)
        self.assertEqual(result.depends_on, [2, 3])
        self.assertEqual(result.tags, ["urgent", "backend"])
        self.assertFalse(result.is_fixed)
        self.assertFalse(result.is_archived)

    def test_convert_to_task_operation_output_with_nulls(self):
        """Test convert_to_task_operation_output with null fields."""
        data = {
            "id": 1,
            "name": "Minimal Task",
            "status": "PENDING",
            "priority": 50,
            "deadline": None,
            "estimated_duration": None,
            "planned_start": None,
            "planned_end": None,
            "actual_start": None,
            "actual_end": None,
            "depends_on": [],
            "tags": [],
            "is_fixed": False,
            "is_archived": False,
            "actual_duration_hours": None,
            "actual_daily_hours": {},
        }

        result = convert_to_task_operation_output(data)

        self.assertEqual(result.id, 1)
        self.assertIsNone(result.deadline)
        self.assertIsNone(result.estimated_duration)
        self.assertIsNone(result.planned_start)
        self.assertEqual(result.depends_on, [])
        self.assertEqual(result.tags, [])

    def test_convert_to_update_task_output(self):
        """Test convert_to_update_task_output."""
        data = {
            "id": 1,
            "name": "Updated Task",
            "status": "IN_PROGRESS",
            "priority": 75,
            "deadline": None,
            "estimated_duration": None,
            "planned_start": None,
            "planned_end": None,
            "actual_start": "2025-01-15T10:00:00",
            "actual_end": None,
            "depends_on": [],
            "tags": ["updated"],
            "is_fixed": False,
            "is_archived": False,
            "actual_duration_hours": None,
            "actual_daily_hours": {},
            "updated_fields": ["name", "status", "tags"],
        }

        result = convert_to_update_task_output(data)

        self.assertEqual(result.task.id, 1)
        self.assertEqual(result.task.name, "Updated Task")
        self.assertEqual(result.task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(result.updated_fields, ["name", "status", "tags"])

    def test_convert_to_task_list_output(self):
        """Test convert_to_task_list_output."""
        data = {
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "priority": 50,
                    "status": "PENDING",
                    "planned_start": None,
                    "planned_end": None,
                    "deadline": "2025-12-31T23:59:00",
                    "actual_start": None,
                    "actual_end": None,
                    "estimated_duration": 5.0,
                    "actual_duration_hours": None,
                    "is_fixed": False,
                    "depends_on": [],
                    "tags": [],
                    "is_archived": False,
                    "is_finished": False,
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-01T00:00:00",
                    "has_notes": False,
                },
                {
                    "id": 2,
                    "name": "Task 2",
                    "priority": 75,
                    "status": "COMPLETED",
                    "planned_start": None,
                    "planned_end": None,
                    "deadline": None,
                    "actual_start": "2025-01-01T09:00:00",
                    "actual_end": "2025-01-01T17:00:00",
                    "estimated_duration": None,
                    "actual_duration_hours": 8.0,
                    "is_fixed": False,
                    "depends_on": [],
                    "tags": ["done"],
                    "is_archived": False,
                    "is_finished": True,
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-01T17:00:00",
                    "has_notes": True,
                },
            ],
            "total_count": 10,
            "filtered_count": 2,
        }

        cache = {}
        result = convert_to_task_list_output(data, cache)

        self.assertEqual(len(result.tasks), 2)
        self.assertEqual(result.total_count, 10)
        self.assertEqual(result.filtered_count, 2)
        self.assertEqual(result.tasks[0].id, 1)
        self.assertEqual(result.tasks[1].id, 2)
        self.assertTrue(result.tasks[1].is_finished)

        # Check cache was populated
        self.assertFalse(cache[1])
        self.assertTrue(cache[2])

    def test_convert_to_get_task_by_id_output(self):
        """Test convert_to_get_task_by_id_output."""
        data = {
            "id": 1,
            "name": "Task Detail",
            "priority": 50,
            "status": "PENDING",
            "planned_start": None,
            "planned_end": None,
            "deadline": "2025-12-31T23:59:00",
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": 5.0,
            "daily_allocations": {"2025-01-15": 2.5, "2025-01-16": 2.5},
            "is_fixed": False,
            "depends_on": [2],
            "actual_daily_hours": {},
            "tags": ["test"],
            "is_archived": False,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "actual_duration_hours": None,
            "is_active": False,
            "is_finished": False,
            "can_be_modified": True,
            "is_schedulable": True,
        }

        result = convert_to_get_task_by_id_output(data)

        self.assertEqual(result.task.id, 1)
        self.assertEqual(result.task.name, "Task Detail")
        self.assertEqual(len(result.task.daily_allocations), 2)
        self.assertTrue(result.task.can_be_modified)

    def test_convert_to_get_task_detail_output(self):
        """Test convert_to_get_task_detail_output."""
        data = {
            "id": 1,
            "name": "Task with Notes",
            "priority": 50,
            "status": "PENDING",
            "planned_start": None,
            "planned_end": None,
            "deadline": None,
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": None,
            "daily_allocations": {},
            "is_fixed": False,
            "depends_on": [],
            "actual_daily_hours": {},
            "tags": [],
            "is_archived": False,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "actual_duration_hours": None,
            "is_active": False,
            "is_finished": False,
            "can_be_modified": True,
            "is_schedulable": True,
            "notes": "# Important notes\n\nSome details here.",
        }

        result = convert_to_get_task_detail_output(data)

        self.assertEqual(result.task.id, 1)
        self.assertEqual(
            result.notes_content, "# Important notes\n\nSome details here."
        )
        self.assertTrue(result.has_notes)

    def test_convert_to_get_task_detail_output_no_notes(self):
        """Test convert_to_get_task_detail_output with no notes."""
        data = {
            "id": 1,
            "name": "Task without Notes",
            "priority": 50,
            "status": "PENDING",
            "planned_start": None,
            "planned_end": None,
            "deadline": None,
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": None,
            "daily_allocations": {},
            "is_fixed": False,
            "depends_on": [],
            "actual_daily_hours": {},
            "tags": [],
            "is_archived": False,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "actual_duration_hours": None,
            "is_active": False,
            "is_finished": False,
            "can_be_modified": True,
            "is_schedulable": True,
            "notes": None,
        }

        result = convert_to_get_task_detail_output(data)

        self.assertIsNone(result.notes_content)
        self.assertFalse(result.has_notes)

    def test_convert_to_tag_statistics_output(self):
        """Test convert_to_tag_statistics_output."""
        data = {
            "tags": [
                {"tag": "urgent", "count": 5, "completion_rate": 0.6},
                {"tag": "backend", "count": 8, "completion_rate": 0.75},
                {"tag": "frontend", "count": 3, "completion_rate": 0.33},
            ],
            "total_tags": 3,
        }

        result = convert_to_tag_statistics_output(data)

        self.assertEqual(result.total_tags, 3)
        self.assertEqual(result.tag_counts["urgent"], 5)
        self.assertEqual(result.tag_counts["backend"], 8)
        self.assertEqual(result.tag_counts["frontend"], 3)

    def test_convert_to_gantt_output(self):
        """Test convert_to_gantt_output."""
        data = {
            "date_range": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "status": "pending",
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
        }

        result = convert_to_gantt_output(data)

        self.assertEqual(result.date_range.start_date.isoformat(), "2025-01-01")
        self.assertEqual(result.date_range.end_date.isoformat(), "2025-01-31")
        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].id, 1)
        self.assertEqual(result.tasks[0].name, "Task 1")
        self.assertEqual(len(result.holidays), 2)
        self.assertIn(datetime(2025, 1, 1).date(), result.holidays)

    def test_convert_to_statistics_output(self):
        """Test convert_to_statistics_output."""
        data = {
            "completion": {
                "total": 100,
                "pending": 20,
                "in_progress": 10,
                "completed": 60,
                "canceled": 10,
                "completion_rate": 0.6,
            },
            "priority": {
                "distribution": {"50": 40, "75": 30, "25": 30},
            },
        }

        result = convert_to_statistics_output(data)

        self.assertEqual(result.task_stats.total_tasks, 100)
        self.assertEqual(result.task_stats.pending_count, 20)
        self.assertEqual(result.task_stats.completed_count, 60)
        self.assertEqual(result.task_stats.completion_rate, 0.6)
        self.assertIsNotNone(result.priority_stats)

    def test_convert_to_optimization_output(self):
        """Test convert_to_optimization_output."""
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

        self.assertEqual(result.summary.new_count, 8)
        self.assertEqual(result.summary.total_hours, 40.0)
        self.assertEqual(len(result.failed_tasks), 2)
        self.assertEqual(result.failed_tasks[0].task.id, 11)
        self.assertEqual(result.failed_tasks[0].reason, "No available time")


class TestConverterErrorHandling(unittest.TestCase):
    """Test cases for error handling in converters (Phase 3 refactoring)."""

    def test_invalid_datetime_format_raises_conversion_error(self):
        """Test that invalid datetime format raises ConversionError."""
        data = {
            "id": 1,
            "name": "Test Task",
            "status": "PENDING",
            "priority": 50,
            "deadline": "invalid-datetime-format",  # Invalid format
            "planned_start": None,
            "planned_end": None,
            "actual_start": None,
            "actual_end": None,
        }

        with self.assertRaises(ConversionError) as context:
            convert_to_task_operation_output(data)

        # Verify error contains field name and value
        self.assertIn("deadline", str(context.exception))
        self.assertEqual(context.exception.field, "deadline")
        self.assertEqual(context.exception.value, "invalid-datetime-format")

    def test_invalid_date_type_raises_conversion_error(self):
        """Test that invalid date type (int instead of string) raises ConversionError."""
        data = {
            "id": 1,
            "name": "Test Task",
            "status": "PENDING",
            "priority": 50,
            "deadline": 12345,  # Invalid type (should be string)
            "planned_start": None,
            "planned_end": None,
            "actual_start": None,
            "actual_end": None,
        }

        with self.assertRaises(ConversionError) as context:
            convert_to_task_operation_output(data)

        self.assertEqual(context.exception.field, "deadline")
        self.assertEqual(context.exception.value, 12345)

    def test_invalid_date_dict_raises_conversion_error(self):
        """Test that invalid date dictionary keys raise ConversionError."""
        data = {
            "id": 1,
            "name": "Test Task",
            "status": "PENDING",
            "priority": 50,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "planned_start": None,
            "planned_end": None,
            "deadline": None,
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": 5.0,
            "is_fixed": False,
            "depends_on": [],
            "tags": [],
            "is_archived": False,
            "is_active": False,
            "is_finished": False,
            "can_be_modified": True,
            "is_schedulable": True,
            "actual_duration_hours": None,
            "daily_allocations": {
                "invalid-date": 2.5,  # Invalid date format
            },
            "actual_daily_hours": {},
        }

        with self.assertRaises(ConversionError) as context:
            convert_to_get_task_by_id_output(data)

        self.assertIn("daily_allocations", str(context.exception))
        self.assertEqual(context.exception.field, "daily_allocations")

    def test_missing_required_datetime_raises_conversion_error(self):
        """Test that missing required datetime field raises ConversionError."""
        data = {
            "id": 1,
            "name": "Test Task",
            "status": "PENDING",
            "priority": 50,
            "planned_start": None,
            "planned_end": None,
            "deadline": None,
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": 5.0,
            "is_fixed": False,
            "depends_on": [],
            "tags": [],
            "is_archived": False,
            "is_active": False,
            "is_finished": False,
            "can_be_modified": True,
            "is_schedulable": True,
            "actual_duration_hours": None,
            "daily_allocations": {},
            "actual_daily_hours": {},
            # Missing "created_at" (required field)
            "updated_at": "2025-01-01T00:00:00",
        }

        with self.assertRaises(ConversionError) as context:
            convert_to_get_task_by_id_output(data)

        self.assertIn("created_at", str(context.exception))
        self.assertEqual(context.exception.field, "created_at")

    def test_none_required_datetime_raises_conversion_error(self):
        """Test that None value for required datetime field raises ConversionError."""
        data = {
            "id": 1,
            "name": "Test Task",
            "status": "PENDING",
            "priority": 50,
            "planned_start": None,
            "planned_end": None,
            "deadline": None,
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": 5.0,
            "is_fixed": False,
            "depends_on": [],
            "tags": [],
            "is_archived": False,
            "is_active": False,
            "is_finished": False,
            "can_be_modified": True,
            "is_schedulable": True,
            "actual_duration_hours": None,
            "daily_allocations": {},
            "actual_daily_hours": {},
            "created_at": None,  # Required but None
            "updated_at": "2025-01-01T00:00:00",
        }

        with self.assertRaises(ConversionError) as context:
            convert_to_get_task_by_id_output(data)

        self.assertIn("created_at", str(context.exception))
        self.assertEqual(context.exception.field, "created_at")
        self.assertIsNone(context.exception.value)

    def test_empty_date_dict_returns_empty_dict(self):
        """Test that empty date dictionary is handled correctly."""
        data = {
            "id": 1,
            "name": "Test Task",
            "status": "PENDING",
            "priority": 50,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "planned_start": None,
            "planned_end": None,
            "deadline": None,
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": 5.0,
            "is_fixed": False,
            "depends_on": [],
            "tags": [],
            "is_archived": False,
            "is_active": False,
            "is_finished": False,
            "can_be_modified": True,
            "is_schedulable": True,
            "actual_duration_hours": None,
            "daily_allocations": {},  # Empty dict
            "actual_daily_hours": {},  # Empty dict
        }

        result = convert_to_get_task_by_id_output(data)

        self.assertEqual(result.task.daily_allocations, {})
        self.assertEqual(result.task.actual_daily_hours, {})

    def test_valid_date_dict_conversion(self):
        """Test that valid date dictionary is converted correctly."""
        data = {
            "id": 1,
            "name": "Test Task",
            "status": "PENDING",
            "priority": 50,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "planned_start": None,
            "planned_end": None,
            "deadline": None,
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": 5.0,
            "is_fixed": False,
            "depends_on": [],
            "tags": [],
            "is_archived": False,
            "is_active": False,
            "is_finished": False,
            "can_be_modified": True,
            "is_schedulable": True,
            "actual_duration_hours": None,
            "daily_allocations": {
                "2025-01-15": 2.5,
                "2025-01-16": 3.0,
            },
            "actual_daily_hours": {
                "2025-01-15": 2.0,
            },
        }

        result = convert_to_get_task_by_id_output(data)

        # Verify date keys are converted to date objects
        from datetime import date

        self.assertEqual(len(result.task.daily_allocations), 2)
        self.assertEqual(result.task.daily_allocations[date(2025, 1, 15)], 2.5)
        self.assertEqual(result.task.daily_allocations[date(2025, 1, 16)], 3.0)
        self.assertEqual(result.task.actual_daily_hours[date(2025, 1, 15)], 2.0)


if __name__ == "__main__":
    unittest.main()
