"""Tests for MarkdownTableExporter."""

from datetime import date, datetime

import pytest

from taskdog.exporters.markdown_table_exporter import MarkdownTableExporter
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus


class TestMarkdownTableExporter:
    """Tests for MarkdownTableExporter class."""

    def _create_task_dto(
        self,
        id: int,
        name: str,
        priority: int,
        status: TaskStatus,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        actual_start: datetime | None = None,
        actual_end: datetime | None = None,
        actual_duration_hours: float | None = None,
        is_fixed: bool = False,
        depends_on: list[int] | None = None,
        tags: list[str] | None = None,
        is_archived: bool = False,
        is_finished: bool = False,
    ) -> TaskRowDto:
        """Helper to create TaskRowDto with default values."""
        return TaskRowDto(
            id=id,
            name=name,
            priority=priority,
            status=status,
            deadline=deadline,
            estimated_duration=estimated_duration,
            planned_start=planned_start,
            planned_end=planned_end,
            actual_start=actual_start,
            actual_end=actual_end,
            actual_duration_hours=actual_duration_hours,
            is_fixed=is_fixed,
            depends_on=depends_on or [],
            tags=tags or [],
            is_archived=is_archived,
            is_finished=is_finished,
            created_at=datetime(2024, 12, 20, 10, 0),
            updated_at=datetime(2024, 12, 20, 10, 0),
        )

    def test_export_creates_markdown_table(self):
        """Test basic markdown table export."""
        tasks = [
            self._create_task_dto(
                id=1,
                name="Task 1",
                priority=5,
                status=TaskStatus.PENDING,
                deadline=datetime(2025, 11, 1, 18, 0, 0),
                estimated_duration=8.0,
            ),
            self._create_task_dto(
                id=2,
                name="Task 2",
                priority=3,
                status=TaskStatus.COMPLETED,
                deadline=datetime(2025, 11, 2, 18, 0, 0),
                estimated_duration=4.0,
                is_finished=True,
            ),
        ]

        exporter = MarkdownTableExporter()
        result = exporter.export(tasks)

        # Check header row
        assert "|Id|Name|Priority|Status|Deadline|" in result

        # Check separator row
        assert "|--|--|--|--|--|" in result

        # Check data rows
        assert "|1|Task 1|5|PENDING|2025-11-01" in result
        assert "|2|Task 2|3|COMPLETED|2025-11-02" in result

    def test_export_with_specific_fields(self):
        """Test markdown export with specific fields."""
        tasks = [
            self._create_task_dto(
                id=1,
                name="Task 1",
                priority=5,
                status=TaskStatus.PENDING,
            ),
        ]

        exporter = MarkdownTableExporter(field_list=["id", "name", "status"])
        result = exporter.export(tasks)

        # Check header contains only specified fields
        assert "|Id|Name|Status|" in result

        # Check that other fields are not present
        assert "Priority" not in result
        assert "Deadline" not in result

    def test_export_handles_none_values(self):
        """Test that None values are displayed as '-'."""
        tasks = [
            self._create_task_dto(
                id=1,
                name="Task 1",
                priority=5,
                status=TaskStatus.PENDING,
                deadline=None,  # No deadline set
                estimated_duration=None,  # No estimate
            ),
        ]

        exporter = MarkdownTableExporter()
        result = exporter.export(tasks)

        # Check that None values are displayed as '-'
        lines = result.split("\n")
        data_row = lines[2]  # First data row (after header and separator)
        assert "|-|" in data_row  # Should contain '-' for None values

    def test_export_formats_datetime_correctly(self):
        """Test datetime formatting in export."""
        tasks = [
            self._create_task_dto(
                id=1,
                name="Task 1",
                priority=5,
                status=TaskStatus.PENDING,
                planned_start=datetime(2025, 10, 31, 9, 0, 0),
                planned_end=datetime(2025, 11, 1, 18, 0, 0),
            ),
        ]

        exporter = MarkdownTableExporter()
        result = exporter.export(tasks)

        # Check datetime format
        assert "2025-10-31 09:00:00" in result
        assert "2025-11-01 18:00:00" in result

    def test_export_handles_empty_task_list(self):
        """Test exporting empty task list."""
        tasks: list[TaskRowDto] = []

        exporter = MarkdownTableExporter()
        result = exporter.export(tasks)

        # Should still have header and separator
        lines = result.split("\n")
        assert len(lines) == 2  # Only header and separator
        assert "|Id|Name|Priority|" in lines[0]
        assert "|--|--|--|" in lines[1]

    def test_format_field_name_converts_snake_case(self):
        """Test field name formatting."""
        exporter = MarkdownTableExporter()

        assert exporter._format_field_name("id") == "Id"
        assert exporter._format_field_name("name") == "Name"
        assert exporter._format_field_name("planned_start") == "Planned Start"
        assert exporter._format_field_name("estimated_duration") == "Estimated Duration"

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, "-"),
            (datetime(2025, 10, 31, 9, 0, 0), "2025-10-31 09:00:00"),
            (date(2025, 10, 31), "2025-10-31"),
            (True, "✓"),
            (False, "✗"),
            ("test", "test"),
            (42, "42"),
            (3.14, "3.14"),
            ({}, "-"),
            ([], "-"),
        ],
        ids=[
            "none",
            "datetime",
            "date",
            "true",
            "false",
            "string",
            "int",
            "float",
            "empty_dict",
            "empty_list",
        ],
    )
    def test_format_value_handles_different_types(self, value, expected):
        """Test value formatting for different types."""
        exporter = MarkdownTableExporter()

        assert exporter._format_value(value) == expected
