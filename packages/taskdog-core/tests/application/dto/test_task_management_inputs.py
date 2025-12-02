"""Tests for task management Input DTOs."""

from datetime import datetime

import pytest

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


class TestSimpleTaskManagementInputs:
    """Test suite for simple task management DTOs (Archive, Restore)."""

    @pytest.mark.parametrize(
        "dto_class",
        [ArchiveTaskInput, RestoreTaskInput],
        ids=["archive", "restore"],
    )
    def test_create_with_task_id(self, dto_class):
        """Test creating DTO with task_id."""
        dto = dto_class(task_id=1)
        assert dto.task_id == 1

    @pytest.mark.parametrize(
        "dto_class",
        [ArchiveTaskInput, RestoreTaskInput],
        ids=["archive", "restore"],
    )
    def test_equality(self, dto_class):
        """Test equality comparison."""
        dto1 = dto_class(task_id=1)
        dto2 = dto_class(task_id=1)
        assert dto1 == dto2


class TestLogHoursInput:
    """Test suite for LogHoursInput DTO."""

    def test_create_with_date(self) -> None:
        """Test creating DTO with specific date."""
        date = datetime(2025, 1, 1)
        dto = LogHoursInput(task_id=1, hours=5.5, date=date)

        assert dto.task_id == 1
        assert dto.hours == 5.5
        assert dto.date == date

    @pytest.mark.parametrize(
        "hours",
        [8.0, 3.5],
        ids=["whole_number", "fractional"],
    )
    def test_create_with_hours(self, hours):
        """Test creating DTO with different hour values."""
        dto = LogHoursInput(task_id=1, hours=hours, date=datetime(2025, 1, 1))
        assert dto.hours == hours

    def test_equality(self) -> None:
        """Test equality comparison."""
        date = datetime(2025, 1, 1)
        dto1 = LogHoursInput(task_id=1, hours=5.0, date=date)
        dto2 = LogHoursInput(task_id=1, hours=5.0, date=date)

        assert dto1 == dto2


class TestDependencyInputs:
    """Test suite for dependency management DTOs."""

    @pytest.mark.parametrize(
        "dto_class",
        [AddDependencyInput, RemoveDependencyInput],
        ids=["add_dependency", "remove_dependency"],
    )
    def test_create_with_dependency_id(self, dto_class):
        """Test creating DTO with task_id and depends_on_id."""
        dto = dto_class(task_id=1, depends_on_id=2)

        assert dto.task_id == 1
        assert dto.depends_on_id == 2

    @pytest.mark.parametrize(
        "dto_class",
        [AddDependencyInput, RemoveDependencyInput],
        ids=["add_dependency", "remove_dependency"],
    )
    def test_equality(self, dto_class):
        """Test equality comparison."""
        dto1 = dto_class(task_id=1, depends_on_id=2)
        dto2 = dto_class(task_id=1, depends_on_id=2)

        assert dto1 == dto2

    def test_add_dependency_task_depends_on_itself_representation(self) -> None:
        """Test that same task_id and depends_on_id is allowed (validation elsewhere)."""
        dto = AddDependencyInput(task_id=1, depends_on_id=1)
        assert dto.task_id == dto.depends_on_id

    def test_add_dependency_inequality_with_different_dependency(self) -> None:
        """Test inequality when depends_on_id differs."""
        dto1 = AddDependencyInput(task_id=1, depends_on_id=2)
        dto2 = AddDependencyInput(task_id=1, depends_on_id=3)

        assert dto1 != dto2


class TestSetTaskTagsInput:
    """Test suite for SetTaskTagsInput DTO."""

    @pytest.mark.parametrize(
        "tags",
        [
            [],
            ["urgent"],
            ["urgent", "backend", "refactoring"],
        ],
        ids=["empty_tags", "single_tag", "multiple_tags"],
    )
    def test_create_with_tags(self, tags):
        """Test creating DTO with various tag configurations."""
        dto = SetTaskTagsInput(task_id=1, tags=tags)
        assert dto.task_id == 1
        assert dto.tags == tags

    def test_tags_preserve_order(self) -> None:
        """Test that tags list preserves order."""
        tags = ["third", "first", "second"]
        dto = SetTaskTagsInput(task_id=1, tags=tags)

        assert dto.tags == ["third", "first", "second"]

    def test_create_with_unicode_tags(self) -> None:
        """Test creating DTO with Unicode tags."""
        dto = SetTaskTagsInput(task_id=1, tags=["日本語", "絵文字🚀"])

        assert dto.tags == ["日本語", "絵文字🚀"]

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = SetTaskTagsInput(task_id=1, tags=["tag1", "tag2"])
        dto2 = SetTaskTagsInput(task_id=1, tags=["tag1", "tag2"])

        assert dto1 == dto2

    def test_inequality_with_different_tags_order(self) -> None:
        """Test inequality when tags order differs."""
        dto1 = SetTaskTagsInput(task_id=1, tags=["tag1", "tag2"])
        dto2 = SetTaskTagsInput(task_id=1, tags=["tag2", "tag1"])

        assert dto1 != dto2
