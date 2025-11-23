"""Tests for SingleTaskInput and its type aliases."""

import unittest

from parameterized import parameterized

from taskdog_core.application.dto.archive_task_input import ArchiveTaskInput
from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.complete_task_input import CompleteTaskInput
from taskdog_core.application.dto.pause_task_input import PauseTaskInput
from taskdog_core.application.dto.remove_task_input import RemoveTaskInput
from taskdog_core.application.dto.start_task_input import StartTaskInput


class TestSingleTaskInput(unittest.TestCase):
    """Test cases for SingleTaskInput base class."""

    def test_instantiation_with_task_id(self):
        """Test SingleTaskInput can be instantiated with task_id."""
        dto = SingleTaskInput(task_id=123)
        self.assertEqual(dto.task_id, 123)

    def test_task_id_field_accessible(self):
        """Test task_id field is accessible."""
        dto = SingleTaskInput(task_id=456)
        self.assertIsInstance(dto.task_id, int)
        self.assertEqual(dto.task_id, 456)


class TestTypeAliases(unittest.TestCase):
    """Test cases for type aliases of SingleTaskInput."""

    @parameterized.expand(
        [
            ("start_task_input", StartTaskInput, 1),
            ("complete_task_input", CompleteTaskInput, 2),
            ("pause_task_input", PauseTaskInput, 3),
            ("remove_task_input", RemoveTaskInput, 4),
            ("archive_task_input", ArchiveTaskInput, 5),
        ]
    )
    def test_alias_is_single_task_input(self, alias_name, dto_class, task_id):
        """Test that type alias is an instance of SingleTaskInput."""
        dto = dto_class(task_id=task_id)
        self.assertIsInstance(dto, SingleTaskInput)
        self.assertEqual(dto.task_id, task_id)

    def test_all_aliases_are_same_type(self):
        """Test all type aliases resolve to the same type."""
        self.assertEqual(StartTaskInput, SingleTaskInput)
        self.assertEqual(CompleteTaskInput, SingleTaskInput)
        self.assertEqual(PauseTaskInput, SingleTaskInput)
        self.assertEqual(RemoveTaskInput, SingleTaskInput)
        self.assertEqual(ArchiveTaskInput, SingleTaskInput)

    def test_aliases_can_be_used_interchangeably(self):
        """Test type aliases can be used interchangeably."""
        dto1 = StartTaskInput(task_id=10)
        dto2 = CompleteTaskInput(task_id=10)
        dto3 = SingleTaskInput(task_id=10)

        # All should have the same task_id value
        self.assertEqual(dto1.task_id, dto2.task_id)
        self.assertEqual(dto2.task_id, dto3.task_id)

        # All should be instances of SingleTaskInput
        self.assertIsInstance(dto1, SingleTaskInput)
        self.assertIsInstance(dto2, SingleTaskInput)
        self.assertIsInstance(dto3, SingleTaskInput)


if __name__ == "__main__":
    unittest.main()
