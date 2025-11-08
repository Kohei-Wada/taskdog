"""Tests for BatchNotesChecker service."""

import unittest
from unittest.mock import MagicMock, Mock

from taskdog.tui.services.batch_notes_checker import BatchNotesChecker


class TestBatchNotesChecker(unittest.TestCase):
    """Test cases for BatchNotesChecker."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_client = Mock()
        self.checker = BatchNotesChecker(self.api_client)

    def test_initial_cache_empty(self):
        """Test that cache is initially empty."""
        self.assertEqual(len(self.checker._cache), 0)

    def test_load_bulk_single_batch(self):
        """Test loading notes for a small number of tasks."""
        # Mock API response
        self.api_client.get_notes_bulk = MagicMock(
            return_value={1: True, 2: False, 3: True}
        )

        task_ids = [1, 2, 3]
        result = self.checker.load_bulk(task_ids)

        # Verify API was called once
        self.api_client.get_notes_bulk.assert_called_once_with([1, 2, 3])

        # Verify result
        self.assertEqual(result, {1: True, 2: False, 3: True})

        # Verify cache was populated
        self.assertEqual(len(self.checker._cache), 3)
        self.assertTrue(self.checker._cache[1])
        self.assertFalse(self.checker._cache[2])
        self.assertTrue(self.checker._cache[3])

    def test_load_bulk_empty_list(self):
        """Test loading notes for empty task list."""
        result = self.checker.load_bulk([])

        # API should not be called
        self.api_client.get_notes_bulk.assert_not_called()

        # Result should be empty
        self.assertEqual(result, {})

    def test_has_notes_from_cache(self):
        """Test retrieving notes status from cache."""
        # Populate cache
        self.checker._cache = {1: True, 2: False, 3: True}

        self.assertTrue(self.checker.has_notes(1))
        self.assertFalse(self.checker.has_notes(2))
        self.assertTrue(self.checker.has_notes(3))

    def test_has_notes_not_in_cache(self):
        """Test retrieving notes status for task not in cache."""
        # Cache is empty
        self.assertEqual(len(self.checker._cache), 0)

        # Should return False for unknown task
        self.assertFalse(self.checker.has_notes(999))

    def test_clear_cache(self):
        """Test clearing the cache."""
        # Populate cache
        self.checker._cache = {1: True, 2: False, 3: True}
        self.assertEqual(len(self.checker._cache), 3)

        # Clear cache
        self.checker.clear_cache()

        # Verify cache is empty
        self.assertEqual(len(self.checker._cache), 0)

    def test_load_bulk_updates_existing_cache(self):
        """Test that load_bulk updates existing cache entries."""
        # Initial cache
        self.checker._cache = {1: False, 2: False}

        # Mock API response with updated values
        self.api_client.get_notes_bulk = MagicMock(
            return_value={1: True, 2: True, 3: False}
        )

        task_ids = [1, 2, 3]
        self.checker.load_bulk(task_ids)

        # Verify cache was updated
        self.assertTrue(self.checker._cache[1])
        self.assertTrue(self.checker._cache[2])
        self.assertFalse(self.checker._cache[3])

    def test_load_bulk_batching_strategy(self):
        """Test that large task lists are handled appropriately."""
        # Create a large list of task IDs (e.g., 200 tasks)
        task_ids = list(range(1, 201))

        # Mock API response
        mock_response = {task_id: (task_id % 3 == 0) for task_id in task_ids}
        self.api_client.get_notes_bulk = MagicMock(return_value=mock_response)

        result = self.checker.load_bulk(task_ids)

        # Verify API was called (implementation will determine batching strategy)
        self.api_client.get_notes_bulk.assert_called()

        # Verify all tasks are in cache
        self.assertEqual(len(self.checker._cache), 200)

        # Verify result matches mock
        self.assertEqual(result, mock_response)

    def test_cache_persistence_across_calls(self):
        """Test that cache persists across multiple has_notes calls."""
        # Populate cache
        self.checker._cache = {1: True, 2: False}

        # Multiple calls should not clear cache
        self.assertTrue(self.checker.has_notes(1))
        self.assertFalse(self.checker.has_notes(2))
        self.assertTrue(self.checker.has_notes(1))

        # Cache should still have 2 entries
        self.assertEqual(len(self.checker._cache), 2)

    def test_has_task_notes_alias(self):
        """Test that has_task_notes is an alias for has_notes."""
        # Populate cache
        self.checker._cache = {1: True, 2: False}

        # has_task_notes should work the same as has_notes
        self.assertTrue(self.checker.has_task_notes(1))
        self.assertFalse(self.checker.has_task_notes(2))
        self.assertFalse(self.checker.has_task_notes(999))


if __name__ == "__main__":
    unittest.main()
