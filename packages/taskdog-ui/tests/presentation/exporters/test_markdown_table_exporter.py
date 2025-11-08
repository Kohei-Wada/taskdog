"""Tests for MarkdownTableExporter."""

import unittest
from datetime import date, datetime

from taskdog.exporters.markdown_table_exporter import MarkdownTableExporter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestMarkdownTableExporter(unittest.TestCase):
    """Tests for MarkdownTableExporter class."""

    def test_export_creates_markdown_table(self):
        """Test basic markdown table export."""
        tasks = [
            Task(
                id=1,
                name="Task 1",
                priority=5,
                status=TaskStatus.PENDING,
                deadline=datetime(2025, 11, 1, 18, 0, 0),
                estimated_duration=8.0,
            ),
            Task(
                id=2,
                name="Task 2",
                priority=3,
                status=TaskStatus.COMPLETED,
                deadline=datetime(2025, 11, 2, 18, 0, 0),
                estimated_duration=4.0,
            ),
        ]

        exporter = MarkdownTableExporter()
        result = exporter.export(tasks)

        # Check header row
        self.assertIn("|Id|Name|Priority|Status|Deadline|", result)

        # Check separator row
        self.assertIn("|--|--|--|--|--|", result)

        # Check data rows
        self.assertIn("|1|Task 1|5|PENDING|2025-11-01", result)
        self.assertIn("|2|Task 2|3|COMPLETED|2025-11-02", result)

    def test_export_with_specific_fields(self):
        """Test markdown export with specific fields."""
        tasks = [
            Task(
                id=1,
                name="Task 1",
                priority=5,
                status=TaskStatus.PENDING,
            ),
        ]

        exporter = MarkdownTableExporter(field_list=["id", "name", "status"])
        result = exporter.export(tasks)

        # Check header contains only specified fields
        self.assertIn("|Id|Name|Status|", result)

        # Check that other fields are not present
        self.assertNotIn("Priority", result)
        self.assertNotIn("Deadline", result)

    def test_export_handles_none_values(self):
        """Test that None values are displayed as '-'."""
        tasks = [
            Task(
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
        self.assertIn("|-|", data_row)  # Should contain '-' for None values

    def test_export_formats_datetime_correctly(self):
        """Test datetime formatting in export."""
        tasks = [
            Task(
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
        self.assertIn("2025-10-31 09:00:00", result)
        self.assertIn("2025-11-01 18:00:00", result)

    def test_export_handles_empty_task_list(self):
        """Test exporting empty task list."""
        tasks = []

        exporter = MarkdownTableExporter()
        result = exporter.export(tasks)

        # Should still have header and separator
        lines = result.split("\n")
        self.assertEqual(len(lines), 2)  # Only header and separator
        self.assertIn("|Id|Name|Priority|", lines[0])
        self.assertIn("|--|--|--|", lines[1])

    def test_export_handles_daily_allocations(self):
        """Test that daily_allocations dict is formatted properly."""
        tasks = [
            Task(
                id=1,
                name="Task 1",
                priority=5,
                status=TaskStatus.PENDING,
                daily_allocations={date(2025, 10, 31): 4.0, date(2025, 11, 1): 4.0},
            ),
        ]

        exporter = MarkdownTableExporter(field_list=["id", "name", "daily_allocations"])
        result = exporter.export(tasks)

        # Check that daily_allocations is formatted (should show some dates)
        self.assertIn("2025-10-31", result)

    def test_format_field_name_converts_snake_case(self):
        """Test field name formatting."""
        exporter = MarkdownTableExporter()

        self.assertEqual(exporter._format_field_name("id"), "Id")
        self.assertEqual(exporter._format_field_name("name"), "Name")
        self.assertEqual(exporter._format_field_name("planned_start"), "Planned Start")
        self.assertEqual(
            exporter._format_field_name("estimated_duration"), "Estimated Duration"
        )

    def test_format_value_handles_different_types(self):
        """Test value formatting for different types."""
        exporter = MarkdownTableExporter()

        # None
        self.assertEqual(exporter._format_value(None), "-")

        # Datetime
        dt = datetime(2025, 10, 31, 9, 0, 0)
        self.assertEqual(exporter._format_value(dt), "2025-10-31 09:00:00")

        # Date
        d = date(2025, 10, 31)
        self.assertEqual(exporter._format_value(d), "2025-10-31")

        # Boolean
        self.assertEqual(exporter._format_value(True), "✓")
        self.assertEqual(exporter._format_value(False), "✗")

        # String
        self.assertEqual(exporter._format_value("test"), "test")

        # Number
        self.assertEqual(exporter._format_value(42), "42")
        self.assertEqual(exporter._format_value(3.14), "3.14")

        # Empty dict
        self.assertEqual(exporter._format_value({}), "-")

        # Empty list
        self.assertEqual(exporter._format_value([]), "-")


if __name__ == "__main__":
    unittest.main()
