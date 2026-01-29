"""Tests for task management Input DTOs."""

import pytest

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.manage_dependencies_input import (
    AddDependencyInput,
    RemoveDependencyInput,
)
from taskdog_core.application.dto.set_task_tags_input import SetTaskTagsInput


class TestSimpleTaskManagementInputs:
    """Test suite for simple task management DTOs (using SingleTaskInput)."""

    def test_create_with_task_id(self):
        """Test creating SingleTaskInput with task_id."""
        dto = SingleTaskInput(task_id=1)
        assert dto.task_id == 1

    def test_equality(self):
        """Test equality comparison."""
        dto1 = SingleTaskInput(task_id=1)
        dto2 = SingleTaskInput(task_id=1)
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
