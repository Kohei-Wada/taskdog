"""Tests for JsonTaskExporter."""

import json
from datetime import datetime

import pytest

from taskdog.exporters.json_task_exporter import JsonTaskExporter
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus


class TestJsonTaskExporter:
    """Test suite for JsonTaskExporter."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.task1 = TaskRowDto(
            id=1,
            name="Test Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=[],
            tags=[],
            estimated_duration=None,
            actual_duration_hours=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            created_at=datetime(2024, 12, 20, 10, 0),
            updated_at=datetime(2024, 12, 20, 10, 0),
            is_archived=False,
            is_finished=False,
        )

        self.task2 = TaskRowDto(
            id=2,
            name="Complete Task",
            priority=2,
            status=TaskStatus.COMPLETED,
            is_fixed=True,
            depends_on=[1],
            tags=["urgent", "backend"],
            estimated_duration=10.5,
            actual_duration_hours=12.0,
            planned_start=datetime(2025, 1, 1, 9, 0),
            planned_end=datetime(2025, 1, 5, 18, 0),
            actual_start=datetime(2025, 1, 1, 9, 30),
            actual_end=datetime(2025, 1, 5, 17, 45),
            deadline=datetime(2025, 1, 10, 23, 59),
            created_at=datetime(2024, 12, 20, 10, 0),
            updated_at=datetime(2025, 1, 5, 18, 0),
            is_archived=False,
            is_finished=True,
        )

    def test_export_returns_json_string(self) -> None:
        """Test export returns valid JSON string."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task1])

        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    def test_export_includes_all_tasks(self) -> None:
        """Test export includes all provided tasks."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task1, self.task2])

        parsed = json.loads(result)
        assert len(parsed) == 2

    def test_export_preserves_task_data(self) -> None:
        """Test export preserves task data correctly."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task1])

        parsed = json.loads(result)
        task_data = parsed[0]
        assert task_data["id"] == 1
        assert task_data["name"] == "Test Task 1"
        assert task_data["priority"] == 1
        assert task_data["status"] == "PENDING"

    def test_export_formats_json_with_indentation(self) -> None:
        """Test export formats JSON with proper indentation."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task1])

        # Should have newlines and indentation
        assert "\n" in result
        assert "    " in result

    def test_export_preserves_unicode_characters(self) -> None:
        """Test export preserves Unicode and emoji characters."""
        task_with_unicode = TaskRowDto(
            id=3,
            name="タスク 🚀 Test",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=False,
            depends_on=[],
            tags=["日本語"],
            estimated_duration=None,
            actual_duration_hours=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            created_at=datetime(2024, 12, 20, 10, 0),
            updated_at=datetime(2024, 12, 20, 10, 0),
            is_archived=False,
            is_finished=False,
        )
        exporter = JsonTaskExporter()

        result = exporter.export([task_with_unicode])

        # Should not be ASCII-encoded
        assert "タスク" in result
        assert "🚀" in result
        assert "日本語" in result

    def test_export_handles_datetime_fields(self) -> None:
        """Test export serializes datetime fields correctly."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task2])

        parsed = json.loads(result)
        task_data = parsed[0]
        # Datetime should be serialized to ISO format strings
        assert "2025-01-10" in task_data["deadline"]
        assert "2025-01-01" in task_data["planned_start"]
        assert "2025-01-05" in task_data["actual_end"]

    def test_export_handles_numeric_fields(self) -> None:
        """Test export preserves numeric fields correctly."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task2])

        parsed = json.loads(result)
        task_data = parsed[0]
        assert task_data["estimated_duration"] == 10.5
        assert task_data["actual_duration_hours"] == 12.0
        assert task_data["priority"] == 2

    def test_export_handles_list_fields(self) -> None:
        """Test export preserves list fields like tags and depends_on."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task2])

        parsed = json.loads(result)
        task_data = parsed[0]
        assert task_data["tags"] == ["urgent", "backend"]
        assert task_data["depends_on"] == [1]

    def test_export_handles_none_values(self) -> None:
        """Test export handles None values correctly."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task1])

        parsed = json.loads(result)
        task_data = parsed[0]
        assert task_data["deadline"] is None
        assert task_data["estimated_duration"] is None
        assert task_data["actual_start"] is None

    def test_export_handles_empty_task_list(self) -> None:
        """Test export handles empty task list gracefully."""
        exporter = JsonTaskExporter()

        result = exporter.export([])

        parsed = json.loads(result)
        assert parsed == []

    def test_export_with_field_list_filters_fields(self) -> None:
        """Test export with field_list only includes specified fields."""
        exporter = JsonTaskExporter(field_list=["id", "name", "priority"])

        result = exporter.export([self.task2])

        parsed = json.loads(result)
        task_data = parsed[0]
        # Should only have specified fields
        assert "id" in task_data
        assert "name" in task_data
        assert "priority" in task_data
        # Should not have other fields
        assert "status" not in task_data
        assert "deadline" not in task_data
        assert "tags" not in task_data

    def test_export_result_can_be_parsed_back(self) -> None:
        """Test exported JSON can be parsed back correctly."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task1, self.task2])

        # Parse back
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["id"] == 1
        assert parsed[0]["name"] == "Test Task 1"
        assert parsed[1]["id"] == 2
        assert parsed[1]["name"] == "Complete Task"

    def test_export_preserves_boolean_fields(self) -> None:
        """Test export preserves boolean fields correctly."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task2])

        parsed = json.loads(result)
        task_data = parsed[0]
        assert task_data["is_fixed"] is True
        assert task_data["is_finished"] is True
        assert task_data["is_archived"] is False

    def test_export_preserves_float_fields(self) -> None:
        """Test export preserves float fields with correct precision."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task2])

        parsed = json.loads(result)
        task_data = parsed[0]
        assert task_data["estimated_duration"] == 10.5
        assert task_data["actual_duration_hours"] == 12.0

    @pytest.mark.parametrize(
        "field",
        [
            "id",
            "name",
            "priority",
            "status",
            "deadline",
            "is_fixed",
            "depends_on",
            "tags",
        ],
        ids=[
            "id",
            "name",
            "priority",
            "status",
            "deadline",
            "is_fixed",
            "depends_on",
            "tags",
        ],
    )
    def test_export_with_all_fields(self, field) -> None:
        """Test export with all available fields."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task2])

        # Should not raise error
        parsed = json.loads(result)
        task_data = parsed[0]
        assert field in task_data

    def test_export_empty_collections(self) -> None:
        """Test export handles empty collections correctly."""
        exporter = JsonTaskExporter()

        result = exporter.export([self.task1])

        parsed = json.loads(result)
        task_data = parsed[0]
        assert task_data["depends_on"] == []
        assert task_data["tags"] == []
