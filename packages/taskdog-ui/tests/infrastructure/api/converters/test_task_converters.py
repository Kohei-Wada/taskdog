"""Tests for task converter functions."""

from datetime import date, datetime

import pytest

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


class TestConvertToTaskOperationOutput:
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

        assert result.id == 1
        assert result.name == "Test Task"
        assert result.status == TaskStatus.PENDING
        assert result.priority == 50
        assert result.deadline == datetime(2025, 12, 31, 23, 59, 0)
        assert result.estimated_duration == 5.0
        assert result.planned_start == datetime(2025, 1, 1, 9, 0, 0)
        assert result.planned_end == datetime(2025, 1, 5, 17, 0, 0)
        assert result.depends_on == [2, 3]
        assert result.tags == ["urgent", "backend"]
        assert result.is_fixed is False
        assert result.is_archived is False

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

        assert result.id == 1
        assert result.deadline is None
        assert result.estimated_duration is None
        assert result.depends_on == []
        assert result.tags == []

    @pytest.mark.parametrize(
        "status_str,expected_status",
        [
            ("PENDING", TaskStatus.PENDING),
            ("IN_PROGRESS", TaskStatus.IN_PROGRESS),
            ("COMPLETED", TaskStatus.COMPLETED),
        ],
        ids=["pending", "in_progress", "completed"],
    )
    def test_status_conversion(self, status_str, expected_status):
        """Test conversion with different statuses."""
        data = {
            "id": 1,
            "name": "Task",
            "status": status_str,
            "priority": 50,
            "deadline": None,
            "estimated_duration": None,
            "planned_start": None,
            "planned_end": None,
            "actual_start": "2025-01-15T10:00:00" if status_str != "PENDING" else None,
            "actual_end": "2025-01-15T17:00:00" if status_str == "COMPLETED" else None,
            "depends_on": [],
            "tags": [],
            "is_fixed": False,
            "is_archived": False,
            "actual_duration_hours": 8.0 if status_str == "COMPLETED" else None,
            "actual_daily_hours": {},
        }

        result = convert_to_task_operation_output(data)

        assert result.status == expected_status

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

        with pytest.raises(ConversionError) as exc_info:
            convert_to_task_operation_output(data)

        assert exc_info.value.field == "deadline"


class TestConvertToUpdateTaskOutput:
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

        assert result.task.id == 1
        assert result.task.name == "Updated Task"
        assert result.task.status == TaskStatus.IN_PROGRESS
        assert result.updated_fields == ["name", "status", "tags"]

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

        assert result.updated_fields == []


class TestConvertToTaskListOutput:
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

        assert len(result.tasks) == 2
        assert result.total_count == 10
        assert result.filtered_count == 2
        assert result.tasks[0].id == 1
        assert result.tasks[0].name == "Task 1"
        assert result.tasks[0].is_finished is False
        assert result.tasks[1].id == 2
        assert result.tasks[1].is_finished is True

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

        assert cache[1] is False
        assert cache[2] is True

    def test_empty_task_list(self):
        """Test conversion with empty task list."""
        data = {
            "tasks": [],
            "total_count": 0,
            "filtered_count": 0,
        }

        result = convert_to_task_list_output(data)

        assert result.tasks == []
        assert result.total_count == 0
        assert result.filtered_count == 0

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

        assert result.gantt_data is not None
        assert result.gantt_data.date_range.start_date == date(2025, 1, 1)


class TestBuildTaskDetailDto:
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

        assert result.id == 1
        assert result.name == "Detail Task"
        assert result.status == TaskStatus.PENDING
        assert len(result.daily_allocations) == 2
        assert result.daily_allocations[date(2025, 1, 5)] == 2.5
        assert result.can_be_modified is True
        assert result.is_schedulable is True

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

        with pytest.raises(ConversionError) as exc_info:
            _build_task_detail_dto(data)

        assert exc_info.value.field == "created_at"


class TestConvertToGetTaskByIdOutput:
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

        assert result.task.id == 1
        assert result.task.name == "Task"


class TestConvertToGetTaskDetailOutput:
    """Test cases for convert_to_get_task_detail_output."""

    @pytest.mark.parametrize(
        "notes_value,expected_has_notes",
        [
            ("# Important\n\nSome details here.", True),
            (None, False),
            ("", False),
        ],
        ids=["with_notes", "none_notes", "empty_notes"],
    )
    def test_notes_handling(self, notes_value, expected_has_notes):
        """Test conversion with different notes values."""
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
            "notes": notes_value,
        }

        result = convert_to_get_task_detail_output(data)

        assert result.task.id == 1
        assert result.has_notes == expected_has_notes
        if notes_value:
            assert result.notes_content == notes_value
