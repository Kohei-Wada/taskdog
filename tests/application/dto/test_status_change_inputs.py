"""Tests for status change Input DTOs."""

import unittest

from application.dto.cancel_task_input import CancelTaskInput
from application.dto.complete_task_input import CompleteTaskInput
from application.dto.pause_task_input import PauseTaskInput
from application.dto.reopen_task_input import ReopenTaskInput
from application.dto.start_task_input import StartTaskInput


class TestStartTaskInput(unittest.TestCase):
    """Test suite for StartTaskInput DTO."""

    def test_create_with_task_id(self) -> None:
        """Test creating DTO with task_id."""
        dto = StartTaskInput(task_id=1)

        self.assertEqual(dto.task_id, 1)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = StartTaskInput(task_id=1)
        dto2 = StartTaskInput(task_id=1)
        dto3 = StartTaskInput(task_id=2)

        self.assertEqual(dto1, dto2)
        self.assertNotEqual(dto1, dto3)

    def test_repr(self) -> None:
        """Test repr includes task_id."""
        dto = StartTaskInput(task_id=42)
        repr_str = repr(dto)

        self.assertIn("task_id=42", repr_str)


class TestCompleteTaskInput(unittest.TestCase):
    """Test suite for CompleteTaskInput DTO."""

    def test_create_with_task_id(self) -> None:
        """Test creating DTO with task_id."""
        dto = CompleteTaskInput(task_id=1)

        self.assertEqual(dto.task_id, 1)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = CompleteTaskInput(task_id=1)
        dto2 = CompleteTaskInput(task_id=1)

        self.assertEqual(dto1, dto2)


class TestPauseTaskInput(unittest.TestCase):
    """Test suite for PauseTaskInput DTO."""

    def test_create_with_task_id(self) -> None:
        """Test creating DTO with task_id."""
        dto = PauseTaskInput(task_id=1)

        self.assertEqual(dto.task_id, 1)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = PauseTaskInput(task_id=1)
        dto2 = PauseTaskInput(task_id=1)

        self.assertEqual(dto1, dto2)


class TestCancelTaskInput(unittest.TestCase):
    """Test suite for CancelTaskInput DTO."""

    def test_create_with_task_id(self) -> None:
        """Test creating DTO with task_id."""
        dto = CancelTaskInput(task_id=1)

        self.assertEqual(dto.task_id, 1)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = CancelTaskInput(task_id=1)
        dto2 = CancelTaskInput(task_id=1)

        self.assertEqual(dto1, dto2)


class TestReopenTaskInput(unittest.TestCase):
    """Test suite for ReopenTaskInput DTO."""

    def test_create_with_task_id(self) -> None:
        """Test creating DTO with task_id."""
        dto = ReopenTaskInput(task_id=1)

        self.assertEqual(dto.task_id, 1)

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = ReopenTaskInput(task_id=1)
        dto2 = ReopenTaskInput(task_id=1)

        self.assertEqual(dto1, dto2)


if __name__ == "__main__":
    unittest.main()
