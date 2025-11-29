"""Tests for task converter functions."""

import unittest
from datetime import date, datetime

from taskdog.infrastructure.api.converters.exceptions import ConversionError
from taskdog.infrastructure.api.converters.task_converters import (
    _build_task_detail_dto,
    convert_to_get_task_by_id_output,
    convert_to_get_task_detail_output,
    convert_to_task_list_output,
    convert_to_task_operation_output,
    convert_to_update_task_output,
)
from taskdog_core.domain.entities.task import TaskStatus


class TestConvertToTaskOperationOutput(unittest.TestCase):
    """Test cases for convert_to_task_operation_output."""

    def test_complete_data(self):
        """Test conversion with all fields populated."""
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
        self.assertEqual(result.planned_start, datetime(2025, 1, 1, 9, 0, 0))
        self.assertEqual(result.planned_end, datetime(2025, 1, 5, 17, 0, 0))
        self.assertEqual(result.depends_on, [2, 3])
        self.assertEqual(result.tags, ["urgent", "backend"])
        self.assertFalse(result.is_fixed)
        self.assertFalse(result.is_archived)

    def test_minimal_data(self):
        """Test conversion with minimal required fields."""
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
        self.assertEqual(result.depends_on, [])
        self.assertEqual(result.tags, [])

    def test_in_progress_status(self):
        """Test conversion with IN_PROGRESS status."""
        data = {
            "id": 1,
            "name": "Active Task",
            "status": "IN_PROGRESS",
            "priority": 75,
            "deadline": None,
            "estimated_duration": None,
            "planned_start": None,
            "planned_end": None,
            "actual_start": "2025-01-15T10:00:00",
            "actual_end": None,
            "depends_on": [],
            "tags": [],
            "is_fixed": False,
            "is_archived": False,
            "actual_duration_hours": None,
            "actual_daily_hours": {},
        }

        result = convert_to_task_operation_output(data)

        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(result.actual_start, datetime(2025, 1, 15, 10, 0, 0))
        self.assertIsNone(result.actual_end)

    def test_completed_status(self):
        """Test conversion with COMPLETED status."""
        data = {
            "id": 1,
            "name": "Done Task",
            "status": "COMPLETED",
            "priority": 50,
            "deadline": None,
            "estimated_duration": 5.0,
            "planned_start": None,
            "planned_end": None,
            "actual_start": "2025-01-15T09:00:00",
            "actual_end": "2025-01-15T17:00:00",
            "depends_on": [],
            "tags": [],
            "is_fixed": False,
            "is_archived": False,
            "actual_duration_hours": 8.0,
            "actual_daily_hours": {"2025-01-15": 8.0},
        }

        result = convert_to_task_operation_output(data)

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.actual_duration_hours, 8.0)

    def test_invalid_datetime_raises_error(self):
        """Test that invalid datetime raises ConversionError."""
        data = {
            "id": 1,
            "name": "Test",
            "status": "PENDING",
            "priority": 50,
            "deadline": "invalid-datetime",
            "planned_start": None,
            "planned_end": None,
            "actual_start": None,
            "actual_end": None,
        }

        with self.assertRaises(ConversionError) as context:
            convert_to_task_operation_output(data)

        self.assertEqual(context.exception.field, "deadline")


class TestConvertToUpdateTaskOutput(unittest.TestCase):
    """Test cases for convert_to_update_task_output."""

    def test_update_with_changed_fields(self):
        """Test conversion with updated_fields list."""
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

    def test_update_empty_updated_fields(self):
        """Test conversion with empty updated_fields."""
        data = {
            "id": 1,
            "name": "Task",
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

        result = convert_to_update_task_output(data)

        self.assertEqual(result.updated_fields, [])


class TestConvertToTaskListOutput(unittest.TestCase):
    """Test cases for convert_to_task_list_output."""

    def test_multiple_tasks(self):
        """Test conversion with multiple tasks."""
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

        result = convert_to_task_list_output(data)

        self.assertEqual(len(result.tasks), 2)
        self.assertEqual(result.total_count, 10)
        self.assertEqual(result.filtered_count, 2)
        self.assertEqual(result.tasks[0].id, 1)
        self.assertEqual(result.tasks[0].name, "Task 1")
        self.assertFalse(result.tasks[0].is_finished)
        self.assertEqual(result.tasks[1].id, 2)
        self.assertTrue(result.tasks[1].is_finished)

    def test_with_has_notes_cache(self):
        """Test that has_notes cache is populated."""
        data = {
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "priority": 50,
                    "status": "PENDING",
                    "planned_start": None,
                    "planned_end": None,
                    "deadline": None,
                    "actual_start": None,
                    "actual_end": None,
                    "estimated_duration": None,
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
                    "priority": 50,
                    "status": "PENDING",
                    "planned_start": None,
                    "planned_end": None,
                    "deadline": None,
                    "actual_start": None,
                    "actual_end": None,
                    "estimated_duration": None,
                    "actual_duration_hours": None,
                    "is_fixed": False,
                    "depends_on": [],
                    "tags": [],
                    "is_archived": False,
                    "is_finished": False,
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-01T00:00:00",
                    "has_notes": True,
                },
            ],
            "total_count": 2,
            "filtered_count": 2,
        }

        cache: dict[int, bool] = {}
        convert_to_task_list_output(data, cache)

        self.assertFalse(cache[1])
        self.assertTrue(cache[2])

    def test_empty_task_list(self):
        """Test conversion with empty task list."""
        data = {
            "tasks": [],
            "total_count": 0,
            "filtered_count": 0,
        }

        result = convert_to_task_list_output(data)

        self.assertEqual(result.tasks, [])
        self.assertEqual(result.total_count, 0)
        self.assertEqual(result.filtered_count, 0)

    def test_with_gantt_data(self):
        """Test conversion with gantt data included."""
        data = {
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "priority": 50,
                    "status": "PENDING",
                    "planned_start": "2025-01-05T09:00:00",
                    "planned_end": "2025-01-10T17:00:00",
                    "deadline": None,
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
            ],
            "total_count": 1,
            "filtered_count": 1,
            "gantt": {
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
                        "deadline": None,
                    }
                ],
                "task_daily_hours": {"1": {"2025-01-05": 2.0}},
                "daily_workload": {"2025-01-05": 2.0},
                "holidays": [],
            },
        }

        result = convert_to_task_list_output(data)

        self.assertIsNotNone(result.gantt_data)
        self.assertEqual(result.gantt_data.date_range.start_date, date(2025, 1, 1))


class TestBuildTaskDetailDto(unittest.TestCase):
    """Test cases for _build_task_detail_dto."""

    def test_complete_data(self):
        """Test building DTO with complete data."""
        data = {
            "id": 1,
            "name": "Detail Task",
            "priority": 50,
            "status": "PENDING",
            "planned_start": "2025-01-05T09:00:00",
            "planned_end": "2025-01-10T17:00:00",
            "deadline": "2025-01-15T23:59:00",
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": 5.0,
            "daily_allocations": {"2025-01-05": 2.5, "2025-01-06": 2.5},
            "is_fixed": False,
            "depends_on": [2, 3],
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

        result = _build_task_detail_dto(data)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "Detail Task")
        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertEqual(len(result.daily_allocations), 2)
        self.assertEqual(result.daily_allocations[date(2025, 1, 5)], 2.5)
        self.assertTrue(result.can_be_modified)
        self.assertTrue(result.is_schedulable)

    def test_missing_required_datetime_raises_error(self):
        """Test that missing required datetime raises error."""
        data = {
            "id": 1,
            "name": "Test",
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
            # Missing created_at
            "updated_at": "2025-01-01T00:00:00",
        }

        with self.assertRaises(ConversionError) as context:
            _build_task_detail_dto(data)

        self.assertEqual(context.exception.field, "created_at")


class TestConvertToGetTaskByIdOutput(unittest.TestCase):
    """Test cases for convert_to_get_task_by_id_output."""

    def test_basic_conversion(self):
        """Test basic conversion."""
        data = {
            "id": 1,
            "name": "Task",
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
        }

        result = convert_to_get_task_by_id_output(data)

        self.assertEqual(result.task.id, 1)
        self.assertEqual(result.task.name, "Task")


class TestConvertToGetTaskDetailOutput(unittest.TestCase):
    """Test cases for convert_to_get_task_detail_output."""

    def test_with_notes(self):
        """Test conversion with notes content."""
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
            "notes": "# Important\n\nSome details here.",
        }

        result = convert_to_get_task_detail_output(data)

        self.assertEqual(result.task.id, 1)
        self.assertEqual(result.notes_content, "# Important\n\nSome details here.")
        self.assertTrue(result.has_notes)

    def test_without_notes(self):
        """Test conversion without notes."""
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

    def test_empty_notes(self):
        """Test conversion with empty notes string."""
        data = {
            "id": 1,
            "name": "Task",
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
            "notes": "",
        }

        result = convert_to_get_task_detail_output(data)

        self.assertFalse(result.has_notes)


if __name__ == "__main__":
    unittest.main()
