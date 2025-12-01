"""Tests for CsvTaskExporter."""

import csv
import io
import unittest
from datetime import datetime

from taskdog.exporters.csv_task_exporter import CsvTaskExporter
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus


class TestCsvTaskExporter(unittest.TestCase):
    """Test suite for CsvTaskExporter."""

    def setUp(self) -> None:
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

    def test_export_returns_csv_string(self) -> None:
        """Test export returns valid CSV string."""
        exporter = CsvTaskExporter()

        result = exporter.export([self.task1])

        self.assertIsInstance(result, str)
        # Should have header and at least one data row
        lines = result.strip().split("\n")
        self.assertGreater(len(lines), 1)

    def test_export_includes_header_row(self) -> None:
        """Test export includes CSV header row with field names."""
        exporter = CsvTaskExporter()

        result = exporter.export([self.task1])

        reader = csv.DictReader(io.StringIO(result))
        fieldnames = reader.fieldnames
        self.assertIsNotNone(fieldnames)
        # Should have at least basic fields
        self.assertIn("id", fieldnames)
        self.assertIn("name", fieldnames)
        self.assertIn("status", fieldnames)

    def test_export_uses_default_fields_when_not_specified(self) -> None:
        """Test export uses DEFAULT_CSV_FIELDS when no fields specified."""
        from taskdog.exporters.csv_task_exporter import DEFAULT_CSV_FIELDS

        exporter = CsvTaskExporter()

        result = exporter.export([self.task1])

        reader = csv.DictReader(io.StringIO(result))
        self.assertEqual(list(reader.fieldnames), list(DEFAULT_CSV_FIELDS))

    def test_export_uses_specified_fields(self) -> None:
        """Test export uses custom field list when provided."""
        custom_fields = ["id", "name", "priority"]
        exporter = CsvTaskExporter(field_list=custom_fields)

        result = exporter.export([self.task1])

        reader = csv.DictReader(io.StringIO(result))
        self.assertEqual(list(reader.fieldnames), custom_fields)

    def test_export_includes_all_tasks(self) -> None:
        """Test export includes all provided tasks."""
        exporter = CsvTaskExporter()

        result = exporter.export([self.task1, self.task2])

        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        self.assertEqual(len(rows), 2)

    def test_export_preserves_task_data(self) -> None:
        """Test export preserves task data correctly."""
        exporter = CsvTaskExporter(field_list=["id", "name", "priority", "status"])

        result = exporter.export([self.task1])

        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        self.assertEqual(row["id"], "1")
        self.assertEqual(row["name"], "Test Task 1")
        self.assertEqual(row["priority"], "1")
        self.assertEqual(row["status"], "PENDING")

    def test_export_handles_datetime_fields(self) -> None:
        """Test export handles datetime fields correctly."""
        exporter = CsvTaskExporter(
            field_list=["id", "deadline", "planned_start", "actual_end"]
        )

        result = exporter.export([self.task2])

        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        # Datetime should be serialized to ISO format
        self.assertIn("2025-01-10", row["deadline"])
        self.assertIn("2025-01-01", row["planned_start"])
        self.assertIn("2025-01-05", row["actual_end"])

    def test_export_handles_list_fields(self) -> None:
        """Test export handles list fields."""
        exporter = CsvTaskExporter(field_list=["id", "tags", "depends_on"])

        result = exporter.export([self.task2])

        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        # Lists should be present in some string representation
        self.assertIsInstance(row["tags"], str)
        self.assertIsInstance(row["depends_on"], str)

    def test_export_handles_empty_task_list(self) -> None:
        """Test export handles empty task list gracefully."""
        exporter = CsvTaskExporter()

        result = exporter.export([])

        # Should have header but no data rows
        lines = result.strip().split("\n")
        self.assertEqual(len(lines), 1)  # Only header

    def test_export_handles_none_values(self) -> None:
        """Test export handles None values correctly."""
        exporter = CsvTaskExporter(field_list=["id", "deadline", "estimated_duration"])

        result = exporter.export([self.task1])

        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        self.assertEqual(row["deadline"], "")
        self.assertEqual(row["estimated_duration"], "")

    def test_export_escapes_special_characters_in_task_name(self) -> None:
        """Test export properly escapes special characters like commas."""
        task_with_comma = TaskRowDto(
            id=3,
            name='Task with comma, quote" and newline\n',
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
        exporter = CsvTaskExporter(field_list=["id", "name"])

        result = exporter.export([task_with_comma])

        # CSV module should properly escape these
        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        self.assertEqual(row["name"], 'Task with comma, quote" and newline\n')

    def test_export_ignores_extra_fields_in_task_dict(self) -> None:
        """Test export ignores fields not in the specified field list."""
        exporter = CsvTaskExporter(field_list=["id", "name"])

        result = exporter.export([self.task2])

        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        # Should only have id and name
        self.assertEqual(set(row.keys()), {"id", "name"})

    def test_export_handles_missing_fields_in_task_dict(self) -> None:
        """Test export fills missing fields with empty string."""
        exporter = CsvTaskExporter(field_list=["id", "name", "nonexistent_field"])

        result = exporter.export([self.task1])

        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        self.assertEqual(row["nonexistent_field"], "")

    def test_export_with_all_fields(self) -> None:
        """Test export with all available fields."""
        all_fields = [
            "id",
            "name",
            "priority",
            "status",
            "deadline",
            "planned_start",
            "planned_end",
            "estimated_duration",
            "actual_start",
            "actual_end",
            "actual_duration_hours",
            "created_at",
            "updated_at",
            "is_fixed",
            "depends_on",
            "tags",
            "is_archived",
            "is_finished",
        ]
        exporter = CsvTaskExporter(field_list=all_fields)

        result = exporter.export([self.task2])

        # Should not raise error and should have all fields
        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        self.assertEqual(len(row), len(all_fields))

    def test_export_result_can_be_parsed_back(self) -> None:
        """Test exported CSV can be parsed back correctly."""
        exporter = CsvTaskExporter(field_list=["id", "name", "priority", "status"])

        result = exporter.export([self.task1, self.task2])

        # Parse back
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], "1")
        self.assertEqual(rows[0]["name"], "Test Task 1")
        self.assertEqual(rows[1]["id"], "2")
        self.assertEqual(rows[1]["name"], "Complete Task")


if __name__ == "__main__":
    unittest.main()
