"""Tests for status change Input DTOs.

Note: All status change operations now use SingleTaskInput directly.
These tests verify that SingleTaskInput works correctly for all status
change scenarios (start, complete, pause, cancel, reopen).
"""

from taskdog_core.application.dto.base import SingleTaskInput


class TestStatusChangeInputs:
    """Test suite for status change operations using SingleTaskInput."""

    def test_create_with_task_id(self):
        """Test creating SingleTaskInput with task_id."""
        dto = SingleTaskInput(task_id=1)
        assert dto.task_id == 1

    def test_equality(self):
        """Test equality comparison."""
        dto1 = SingleTaskInput(task_id=1)
        dto2 = SingleTaskInput(task_id=1)
        dto3 = SingleTaskInput(task_id=2)

        assert dto1 == dto2
        assert dto1 != dto3

    def test_repr(self) -> None:
        """Test repr includes task_id."""
        dto = SingleTaskInput(task_id=42)
        repr_str = repr(dto)

        assert "task_id=42" in repr_str
