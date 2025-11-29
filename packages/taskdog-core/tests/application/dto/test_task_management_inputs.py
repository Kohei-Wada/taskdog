"""Tests for task management Input DTOs."""

import unittest
from datetime import datetime

from parameterized import parameterized

from taskdog_core.application.dto.log_hours_input import LogHoursInput
from taskdog_core.application.dto.manage_dependencies_input import (
    AddDependencyInput,
    RemoveDependencyInput,
)
from taskdog_core.application.dto.set_task_tags_input import SetTaskTagsInput
from taskdog_core.application.dto.single_task_inputs import (
    ArchiveTaskInput,
    RestoreTaskInput,
)


class TestSimpleTaskManagementInputs(unittest.TestCase):
    """Test suite for simple task management DTOs (Archive, Restore)."""

    @parameterized.expand(
        [
            ("archive", ArchiveTaskInput),
            ("restore", RestoreTaskInput),
        ]
    )
    def test_create_with_task_id(self, operation_name, dto_class):
        """Test creating DTO with task_id."""
        dto = dto_class(task_id=1)
        self.assertEqual(dto.task_id, 1)

    @parameterized.expand(
        [
            ("archive", ArchiveTaskInput),
            ("restore", RestoreTaskInput),
        ]
    )
    def test_equality(self, operation_name, dto_class):
        """Test equality comparison."""
        dto1 = dto_class(task_id=1)
        dto2 = dto_class(task_id=1)
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

    @parameterized.expand(
        [
            ("whole_number", 8.0),
            ("fractional", 3.5),
        ]
    )
    def test_create_with_hours(self, scenario, hours):
        """Test creating DTO with different hour values."""
        dto = LogHoursInput(task_id=1, hours=hours, date=datetime(2025, 1, 1))
        self.assertEqual(dto.hours, hours)

    def test_equality(self) -> None:
        """Test equality comparison."""
        date = datetime(2025, 1, 1)
        dto1 = LogHoursInput(task_id=1, hours=5.0, date=date)
        dto2 = LogHoursInput(task_id=1, hours=5.0, date=date)

        self.assertEqual(dto1, dto2)


class TestDependencyInputs(unittest.TestCase):
    """Test suite for dependency management DTOs."""

    @parameterized.expand(
        [
            ("add_dependency", AddDependencyInput),
            ("remove_dependency", RemoveDependencyInput),
        ]
    )
    def test_create_with_dependency_id(self, operation_name, dto_class):
        """Test creating DTO with task_id and depends_on_id."""
        dto = dto_class(task_id=1, depends_on_id=2)

        self.assertEqual(dto.task_id, 1)
        self.assertEqual(dto.depends_on_id, 2)

    @parameterized.expand(
        [
            ("add_dependency", AddDependencyInput),
            ("remove_dependency", RemoveDependencyInput),
        ]
    )
    def test_equality(self, operation_name, dto_class):
        """Test equality comparison."""
        dto1 = dto_class(task_id=1, depends_on_id=2)
        dto2 = dto_class(task_id=1, depends_on_id=2)

        self.assertEqual(dto1, dto2)

    def test_add_dependency_task_depends_on_itself_representation(self) -> None:
        """Test that same task_id and depends_on_id is allowed (validation elsewhere)."""
        dto = AddDependencyInput(task_id=1, depends_on_id=1)
        self.assertEqual(dto.task_id, dto.depends_on_id)

    def test_add_dependency_inequality_with_different_dependency(self) -> None:
        """Test inequality when depends_on_id differs."""
        dto1 = AddDependencyInput(task_id=1, depends_on_id=2)
        dto2 = AddDependencyInput(task_id=1, depends_on_id=3)

        self.assertNotEqual(dto1, dto2)


class TestSetTaskTagsInput(unittest.TestCase):
    """Test suite for SetTaskTagsInput DTO."""

    @parameterized.expand(
        [
            ("empty_tags", []),
            ("single_tag", ["urgent"]),
            ("multiple_tags", ["urgent", "backend", "refactoring"]),
        ]
    )
    def test_create_with_tags(self, scenario, tags):
        """Test creating DTO with various tag configurations."""
        dto = SetTaskTagsInput(task_id=1, tags=tags)
        self.assertEqual(dto.task_id, 1)
        self.assertEqual(dto.tags, tags)

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
