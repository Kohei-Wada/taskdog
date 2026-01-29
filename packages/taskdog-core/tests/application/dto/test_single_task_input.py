"""Tests for SingleTaskInput."""

from taskdog_core.application.dto.base import SingleTaskInput


class TestSingleTaskInput:
    """Test cases for SingleTaskInput base class."""

    def test_instantiation_with_task_id(self):
        """Test SingleTaskInput can be instantiated with task_id."""
        dto = SingleTaskInput(task_id=123)
        assert dto.task_id == 123

    def test_task_id_field_accessible(self):
        """Test task_id field is accessible."""
        dto = SingleTaskInput(task_id=456)
        assert isinstance(dto.task_id, int)
        assert dto.task_id == 456

    def test_equality(self):
        """Test equality comparison."""
        dto1 = SingleTaskInput(task_id=1)
        dto2 = SingleTaskInput(task_id=1)
        dto3 = SingleTaskInput(task_id=2)

        assert dto1 == dto2
        assert dto1 != dto3

    def test_repr(self):
        """Test repr includes task_id."""
        dto = SingleTaskInput(task_id=42)
        repr_str = repr(dto)

        assert "task_id=42" in repr_str
