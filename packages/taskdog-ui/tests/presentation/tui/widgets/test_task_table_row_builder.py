"""Tests for TaskTableRowBuilder."""

import unittest
from datetime import datetime, timedelta

from rich.text import Text

from taskdog.tui.widgets.task_table_row_builder import TaskTableRowBuilder
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)


class TestTaskTableRowBuilder(unittest.TestCase):
    """Test TaskTableRowBuilder row construction functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.notes_repo = FileNotesRepository()
        self.builder = TaskTableRowBuilder()

    def test_build_row_basic_task(self):
        """Test building a row for a basic task."""
        task = Task(
            id=1,
            name="Test task",
            priority=2,
            status=TaskStatus.PENDING,
        )

        row = self.builder.build_row(task)

        # Should return tuple of 15 Text objects (15 columns)
        self.assertEqual(len(row), 15)
        self.assertIsInstance(row[0], Text)  # ID
        self.assertIsInstance(row[1], Text)  # Name
        self.assertIsInstance(row[3], Text)  # Priority

        # Check basic values
        self.assertEqual(str(row[0]), "1")  # ID
        self.assertEqual(str(row[1]), "Test task")  # Name
        self.assertEqual(str(row[3]), "2")  # Priority

    def test_build_row_completed_task_has_strikethrough(self):
        """Test that completed tasks have strikethrough style on name."""
        task = Task(
            id=1,
            name="Completed task",
            priority=1,
            status=TaskStatus.COMPLETED,
        )

        row = self.builder.build_row(task)

        # Name column should have strikethrough style
        name_text = row[1]
        self.assertEqual(name_text.style, "strike")

    def test_build_row_pending_task_no_strikethrough(self):
        """Test that non-completed tasks don't have strikethrough."""
        task = Task(
            id=1,
            name="Pending task",
            priority=1,
            status=TaskStatus.PENDING,
        )

        row = self.builder.build_row(task)

        # Name column should not have strikethrough
        name_text = row[1]
        self.assertIsNone(name_text.style)

    def test_build_row_fixed_task_shows_flag(self):
        """Test that fixed tasks show the fixed indicator."""
        task = Task(
            id=1,
            name="Fixed task",
            priority=1,
            status=TaskStatus.PENDING,
            is_fixed=True,
        )

        row = self.builder.build_row(task)

        # Flags column should contain fixed indicator
        flags = str(row[4])
        self.assertIn("📌", flags)

    def test_build_row_with_tags(self):
        """Test building a row with tags."""
        task = Task(
            id=1,
            name="Tagged task",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent", "backend"],
        )

        row = self.builder.build_row(task)

        # Tags column should show comma-separated tags
        tags_text = str(row[14])
        self.assertEqual(tags_text, "urgent, backend")

    def test_build_row_with_deadline(self):
        """Test building a row with deadline."""
        deadline = datetime.now() + timedelta(days=7)
        task = Task(
            id=1,
            name="Task with deadline",
            priority=1,
            status=TaskStatus.PENDING,
            deadline=deadline,
        )

        row = self.builder.build_row(task)

        # Deadline column should be formatted (not "-")
        deadline_text = str(row[7])
        self.assertNotEqual(deadline_text, "-")

    def test_build_row_with_dependencies(self):
        """Test building a row with dependencies."""
        task = Task(
            id=3,
            name="Dependent task",
            priority=1,
            status=TaskStatus.PENDING,
            depends_on=[1, 2],
        )

        row = self.builder.build_row(task)

        # Dependencies column should show comma-separated IDs
        deps_text = str(row[13])
        self.assertEqual(deps_text, "1,2")

    def test_format_name_truncation(self):
        """Test name truncation for long task names."""
        long_name = "A" * 100  # Very long name

        formatted = self.builder._format_name(long_name)

        # Should be truncated with "..."
        self.assertTrue(formatted.endswith("..."))
        self.assertLess(len(formatted), len(long_name))

    def test_format_name_no_truncation(self):
        """Test that short names are not truncated."""
        short_name = "Short task"

        formatted = self.builder._format_name(short_name)

        self.assertEqual(formatted, short_name)

    def test_format_tags_truncation(self):
        """Test tags truncation for long tag lists."""
        long_tags = ["tag1", "tag2", "tag3", "tag4", "tag5", "verylongtag"]

        formatted = self.builder._format_tags(long_tags)

        # Should be truncated with "..."
        self.assertTrue(formatted.endswith("..."))

    def test_format_tags_empty(self):
        """Test formatting empty tags."""
        formatted = self.builder._format_tags(None)
        self.assertEqual(formatted, "")

        formatted = self.builder._format_tags([])
        self.assertEqual(formatted, "")

    def test_format_tags_no_truncation(self):
        """Test that short tag lists are not truncated."""
        short_tags = ["tag1", "tag2"]

        formatted = self.builder._format_tags(short_tags)

        self.assertEqual(formatted, "tag1, tag2")

    def test_build_row_in_progress_task_shows_elapsed_time(self):
        """Test that IN_PROGRESS tasks show elapsed time."""
        task = Task(
            id=1,
            name="In progress task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime.now() - timedelta(hours=2),
        )

        row = self.builder.build_row(task)

        # Elapsed time column should show time (not "-")
        elapsed_text = str(row[12])
        self.assertNotEqual(elapsed_text, "-")

    def test_build_row_with_estimated_duration(self):
        """Test building a row with estimated duration."""
        task = Task(
            id=1,
            name="Task with estimate",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=8,
        )

        row = self.builder.build_row(task)

        # Duration column should show estimate
        duration_text = str(row[5])
        self.assertIn("E:8h", duration_text)


if __name__ == "__main__":
    unittest.main()
