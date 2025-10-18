"""Tests for SingleTaskInput and its type aliases."""

import unittest

from application.dto.archive_task_input import ArchiveTaskInput
from application.dto.base import SingleTaskInput
from application.dto.complete_task_input import CompleteTaskInput
from application.dto.pause_task_input import PauseTaskInput
from application.dto.remove_task_input import RemoveTaskInput
from application.dto.start_task_input import StartTaskInput


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

    def test_start_task_input_is_single_task_input(self):
        """Test StartTaskInput is an alias of SingleTaskInput."""
        dto = StartTaskInput(task_id=1)
        self.assertIsInstance(dto, SingleTaskInput)
        self.assertEqual(dto.task_id, 1)

    def test_complete_task_input_is_single_task_input(self):
        """Test CompleteTaskInput is an alias of SingleTaskInput."""
        dto = CompleteTaskInput(task_id=2)
        self.assertIsInstance(dto, SingleTaskInput)
        self.assertEqual(dto.task_id, 2)

    def test_pause_task_input_is_single_task_input(self):
        """Test PauseTaskInput is an alias of SingleTaskInput."""
        dto = PauseTaskInput(task_id=3)
        self.assertIsInstance(dto, SingleTaskInput)
        self.assertEqual(dto.task_id, 3)

    def test_remove_task_input_is_single_task_input(self):
        """Test RemoveTaskInput is an alias of SingleTaskInput."""
        dto = RemoveTaskInput(task_id=4)
        self.assertIsInstance(dto, SingleTaskInput)
        self.assertEqual(dto.task_id, 4)

    def test_archive_task_input_is_single_task_input(self):
        """Test ArchiveTaskInput is an alias of SingleTaskInput."""
        dto = ArchiveTaskInput(task_id=5)
        self.assertIsInstance(dto, SingleTaskInput)
        self.assertEqual(dto.task_id, 5)

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
