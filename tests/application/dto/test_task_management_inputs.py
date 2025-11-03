"""Tests for task management Input DTOs."""

import unittest
from datetime import datetime

from application.dto.archive_task_input import ArchiveTaskInput
from application.dto.log_hours_input import LogHoursInput
from application.dto.manage_dependencies_input import AddDependencyInput, RemoveDependencyInput
from application.dto.restore_task_input import RestoreTaskInput
from application.dto.set_task_tags_input import SetTaskTagsInput


class TestArchiveTaskInput(unittest.TestCase):
    """Test suite for ArchiveTaskInput DTO."""

    def test_create_with_task_id(self) -> None:
        """Test creating DTO with task_id."""
        dto = ArchiveTaskInput(task_id=1)

        self.assertEqual(dto.task_id, 1)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = ArchiveTaskInput(task_id=1)
        dto2 = ArchiveTaskInput(task_id=1)

        self.assertEqual(dto1, dto2)


class TestRestoreTaskInput(unittest.TestCase):
    """Test suite for RestoreTaskInput DTO."""

    def test_create_with_task_id(self) -> None:
        """Test creating DTO with task_id."""
        dto = RestoreTaskInput(task_id=1)

        self.assertEqual(dto.task_id, 1)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = RestoreTaskInput(task_id=1)
        dto2 = RestoreTaskInput(task_id=1)

        self.assertEqual(dto1, dto2)


class TestLogHoursInput(unittest.TestCase):
    """Test suite for LogHoursInput DTO."""

    def test_create_with_date(self) -> None:
        """Test creating DTO with specific date."""
        date = datetime(2025, 1, 1)
        dto = LogHoursInput(task_id=1, hours=5.5, date=date)

        self.assertEqual(dto.task_id, 1)
        self.assertEqual(dto.hours, 5.5)
        self.assertEqual(dto.date, date)

    def test_create_with_whole_number_hours(self) -> None:
        """Test creating DTO with whole number hours."""
        dto = LogHoursInput(task_id=1, hours=8.0, date=datetime(2025, 1, 1))

        self.assertEqual(dto.hours, 8.0)

    def test_create_with_fractional_hours(self) -> None:
        """Test creating DTO with fractional hours."""
        dto = LogHoursInput(task_id=1, hours=3.5, date=datetime(2025, 1, 1))

        self.assertEqual(dto.hours, 3.5)

    def test_equality(self) -> None:
        """Test equality comparison."""
        date = datetime(2025, 1, 1)
        dto1 = LogHoursInput(task_id=1, hours=5.0, date=date)
        dto2 = LogHoursInput(task_id=1, hours=5.0, date=date)

        self.assertEqual(dto1, dto2)


class TestAddDependencyInput(unittest.TestCase):
    """Test suite for AddDependencyInput DTO."""

    def test_create_with_dependency_id(self) -> None:
        """Test creating DTO with task_id and depends_on_id."""
        dto = AddDependencyInput(task_id=1, depends_on_id=2)

        self.assertEqual(dto.task_id, 1)
        self.assertEqual(dto.depends_on_id, 2)

    def test_task_depends_on_itself_representation(self) -> None:
        """Test that same task_id and depends_on_id is allowed (validation elsewhere)."""
        dto = AddDependencyInput(task_id=1, depends_on_id=1)

        self.assertEqual(dto.task_id, dto.depends_on_id)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = AddDependencyInput(task_id=1, depends_on_id=2)
        dto2 = AddDependencyInput(task_id=1, depends_on_id=2)

        self.assertEqual(dto1, dto2)

    def test_inequality_with_different_dependency(self) -> None:
        """Test inequality when depends_on_id differs."""
        dto1 = AddDependencyInput(task_id=1, depends_on_id=2)
        dto2 = AddDependencyInput(task_id=1, depends_on_id=3)

        self.assertNotEqual(dto1, dto2)


class TestRemoveDependencyInput(unittest.TestCase):
    """Test suite for RemoveDependencyInput DTO."""

    def test_create_with_dependency_id(self) -> None:
        """Test creating DTO with task_id and depends_on_id."""
        dto = RemoveDependencyInput(task_id=1, depends_on_id=2)

        self.assertEqual(dto.task_id, 1)
        self.assertEqual(dto.depends_on_id, 2)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = RemoveDependencyInput(task_id=1, depends_on_id=2)
        dto2 = RemoveDependencyInput(task_id=1, depends_on_id=2)

        self.assertEqual(dto1, dto2)


class TestSetTaskTagsInput(unittest.TestCase):
    """Test suite for SetTaskTagsInput DTO."""

    def test_create_with_empty_tags(self) -> None:
        """Test creating DTO with empty tags list."""
        dto = SetTaskTagsInput(task_id=1, tags=[])

        self.assertEqual(dto.task_id, 1)
        self.assertEqual(dto.tags, [])

    def test_create_with_single_tag(self) -> None:
        """Test creating DTO with single tag."""
        dto = SetTaskTagsInput(task_id=1, tags=["urgent"])

        self.assertEqual(dto.tags, ["urgent"])

    def test_create_with_multiple_tags(self) -> None:
        """Test creating DTO with multiple tags."""
        dto = SetTaskTagsInput(task_id=1, tags=["urgent", "backend", "refactoring"])

        self.assertEqual(len(dto.tags), 3)
        self.assertEqual(dto.tags, ["urgent", "backend", "refactoring"])

    def test_tags_preserve_order(self) -> None:
        """Test that tags list preserves order."""
        tags = ["third", "first", "second"]
        dto = SetTaskTagsInput(task_id=1, tags=tags)

        self.assertEqual(dto.tags, ["third", "first", "second"])

    def test_create_with_unicode_tags(self) -> None:
        """Test creating DTO with Unicode tags."""
        dto = SetTaskTagsInput(task_id=1, tags=["日本語", "絵文字🚀"])

        self.assertEqual(dto.tags, ["日本語", "絵文字🚀"])

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = SetTaskTagsInput(task_id=1, tags=["tag1", "tag2"])
        dto2 = SetTaskTagsInput(task_id=1, tags=["tag1", "tag2"])

        self.assertEqual(dto1, dto2)

    def test_inequality_with_different_tags_order(self) -> None:
        """Test inequality when tags order differs."""
        dto1 = SetTaskTagsInput(task_id=1, tags=["tag1", "tag2"])
        dto2 = SetTaskTagsInput(task_id=1, tags=["tag2", "tag1"])

        self.assertNotEqual(dto1, dto2)


if __name__ == "__main__":
    unittest.main()
