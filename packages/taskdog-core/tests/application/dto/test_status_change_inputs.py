"""Tests for status change Input DTOs."""

import unittest

from parameterized import parameterized

from taskdog_core.application.dto.cancel_task_input import CancelTaskInput
from taskdog_core.application.dto.complete_task_input import CompleteTaskInput
from taskdog_core.application.dto.pause_task_input import PauseTaskInput
from taskdog_core.application.dto.reopen_task_input import ReopenTaskInput
from taskdog_core.application.dto.start_task_input import StartTaskInput


class TestStatusChangeInputs(unittest.TestCase):
    """Test suite for all status change Input DTOs."""

    @parameterized.expand(
        [
            ("start", StartTaskInput),
            ("complete", CompleteTaskInput),
            ("pause", PauseTaskInput),
            ("cancel", CancelTaskInput),
            ("reopen", ReopenTaskInput),
        ]
    )
    def test_create_with_task_id(self, operation_name, dto_class):
        """Test creating DTO with task_id."""
        dto = dto_class(task_id=1)

        self.assertEqual(dto.task_id, 1)

    @parameterized.expand(
        [
            ("start", StartTaskInput),
            ("complete", CompleteTaskInput),
            ("pause", PauseTaskInput),
            ("cancel", CancelTaskInput),
            ("reopen", ReopenTaskInput),
        ]
    )
    def test_equality(self, operation_name, dto_class):
        """Test equality comparison."""
        dto1 = dto_class(task_id=1)
        dto2 = dto_class(task_id=1)
        dto3 = dto_class(task_id=2)

        self.assertEqual(dto1, dto2)
        self.assertNotEqual(dto1, dto3)

    def test_start_task_input_repr(self) -> None:
        """Test repr includes task_id for StartTaskInput."""
        dto = StartTaskInput(task_id=42)
        repr_str = repr(dto)

        self.assertIn("task_id=42", repr_str)


if __name__ == "__main__":
    unittest.main()
