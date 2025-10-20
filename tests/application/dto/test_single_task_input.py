"""Tests for SingleTaskRequest and its type aliases."""

import unittest

from application.dto.archive_task_request import ArchiveTaskRequest
from application.dto.base import SingleTaskRequest
from application.dto.complete_task_request import CompleteTaskRequest
from application.dto.pause_task_request import PauseTaskRequest
from application.dto.remove_task_request import RemoveTaskRequest
from application.dto.start_task_request import StartTaskRequest


class TestSingleTaskInput(unittest.TestCase):
    """Test cases for SingleTaskRequest base class."""

    def test_instantiation_with_task_id(self):
        """Test SingleTaskRequest can be instantiated with task_id."""
        dto = SingleTaskRequest(task_id=123)
        self.assertEqual(dto.task_id, 123)

    def test_task_id_field_accessible(self):
        """Test task_id field is accessible."""
        dto = SingleTaskRequest(task_id=456)
        self.assertIsInstance(dto.task_id, int)
        self.assertEqual(dto.task_id, 456)


class TestTypeAliases(unittest.TestCase):
    """Test cases for type aliases of SingleTaskRequest."""

    def test_start_task_input_is_single_task_input(self):
        """Test StartTaskRequest is an alias of SingleTaskRequest."""
        dto = StartTaskRequest(task_id=1)
        self.assertIsInstance(dto, SingleTaskRequest)
        self.assertEqual(dto.task_id, 1)

    def test_complete_task_input_is_single_task_input(self):
        """Test CompleteTaskRequest is an alias of SingleTaskRequest."""
        dto = CompleteTaskRequest(task_id=2)
        self.assertIsInstance(dto, SingleTaskRequest)
        self.assertEqual(dto.task_id, 2)

    def test_pause_task_input_is_single_task_input(self):
        """Test PauseTaskRequest is an alias of SingleTaskRequest."""
        dto = PauseTaskRequest(task_id=3)
        self.assertIsInstance(dto, SingleTaskRequest)
        self.assertEqual(dto.task_id, 3)

    def test_remove_task_input_is_single_task_input(self):
        """Test RemoveTaskRequest is an alias of SingleTaskRequest."""
        dto = RemoveTaskRequest(task_id=4)
        self.assertIsInstance(dto, SingleTaskRequest)
        self.assertEqual(dto.task_id, 4)

    def test_archive_task_input_is_single_task_input(self):
        """Test ArchiveTaskRequest is an alias of SingleTaskRequest."""
        dto = ArchiveTaskRequest(task_id=5)
        self.assertIsInstance(dto, SingleTaskRequest)
        self.assertEqual(dto.task_id, 5)

    def test_all_aliases_are_same_type(self):
        """Test all type aliases resolve to the same type."""
        self.assertEqual(StartTaskRequest, SingleTaskRequest)
        self.assertEqual(CompleteTaskRequest, SingleTaskRequest)
        self.assertEqual(PauseTaskRequest, SingleTaskRequest)
        self.assertEqual(RemoveTaskRequest, SingleTaskRequest)
        self.assertEqual(ArchiveTaskRequest, SingleTaskRequest)

    def test_aliases_can_be_used_interchangeably(self):
        """Test type aliases can be used interchangeably."""
        dto1 = StartTaskRequest(task_id=10)
        dto2 = CompleteTaskRequest(task_id=10)
        dto3 = SingleTaskRequest(task_id=10)

        # All should have the same task_id value
        self.assertEqual(dto1.task_id, dto2.task_id)
        self.assertEqual(dto2.task_id, dto3.task_id)

        # All should be instances of SingleTaskRequest
        self.assertIsInstance(dto1, SingleTaskRequest)
        self.assertIsInstance(dto2, SingleTaskRequest)
        self.assertIsInstance(dto3, SingleTaskRequest)


if __name__ == "__main__":
    unittest.main()
