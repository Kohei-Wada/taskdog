"""Tests for TagFilter."""

import unittest

from application.queries.filters.tag_filter import TagFilter
from domain.entities.task import Task, TaskStatus


class TestTagFilter(unittest.TestCase):
    """Test cases for TagFilter."""

    def setUp(self):
        """Create sample tasks for testing."""
        self.task1 = Task(
            id=1, name="Task 1", status=TaskStatus.PENDING, priority=1, tags=["work", "urgent"]
        )
        self.task2 = Task(
            id=2, name="Task 2", status=TaskStatus.PENDING, priority=1, tags=["personal"]
        )
        self.task3 = Task(
            id=3, name="Task 3", status=TaskStatus.PENDING, priority=1, tags=["work", "bug"]
        )
        self.task4 = Task(id=4, name="Task 4", status=TaskStatus.PENDING, priority=1, tags=[])
        self.tasks = [self.task1, self.task2, self.task3, self.task4]

    def test_filter_or_logic_single_tag(self):
        """Test filter with OR logic (match_all=False) and single tag."""
        tag_filter = TagFilter(tags=["work"], match_all=False)
        result = tag_filter.filter(self.tasks)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 3)

    def test_filter_or_logic_multiple_tags(self):
        """Test filter with OR logic (match_all=False) and multiple tags."""
        tag_filter = TagFilter(tags=["work", "personal"], match_all=False)
        result = tag_filter.filter(self.tasks)

        # Should match tasks with tag "work" OR "personal"
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[2].id, 3)

    def test_filter_and_logic_single_tag(self):
        """Test filter with AND logic (match_all=True) and single tag."""
        tag_filter = TagFilter(tags=["work"], match_all=True)
        result = tag_filter.filter(self.tasks)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 3)

    def test_filter_and_logic_multiple_tags(self):
        """Test filter with AND logic (match_all=True) and multiple tags."""
        tag_filter = TagFilter(tags=["work", "urgent"], match_all=True)
        result = tag_filter.filter(self.tasks)

        # Should match only tasks with BOTH "work" AND "urgent"
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_filter_and_logic_no_match(self):
        """Test filter with AND logic where no task has all tags."""
        tag_filter = TagFilter(tags=["work", "personal"], match_all=True)
        result = tag_filter.filter(self.tasks)

        # No task has both "work" AND "personal"
        self.assertEqual(len(result), 0)

    def test_filter_with_empty_tags(self):
        """Test filter with empty tags list returns all tasks."""
        tag_filter = TagFilter(tags=[], match_all=False)
        result = tag_filter.filter(self.tasks)

        self.assertEqual(len(result), 4)

    def test_filter_with_nonexistent_tag(self):
        """Test filter with tag that doesn't exist in any task."""
        tag_filter = TagFilter(tags=["nonexistent"], match_all=False)
        result = tag_filter.filter(self.tasks)

        self.assertEqual(len(result), 0)

    def test_filter_with_empty_task_list(self):
        """Test filter with empty task list."""
        tag_filter = TagFilter(tags=["work"], match_all=False)
        result = tag_filter.filter([])

        self.assertEqual(len(result), 0)

    def test_filter_excludes_tasks_without_tags(self):
        """Test that tasks with no tags are excluded when filtering by tags."""
        tag_filter = TagFilter(tags=["work"], match_all=False)
        result = tag_filter.filter(self.tasks)

        # task4 has no tags, should not be included
        self.assertNotIn(self.task4, result)

    def test_filter_stores_tags_and_match_all(self):
        """Test that filter stores tags and match_all settings."""
        tag_filter = TagFilter(tags=["work", "urgent"], match_all=True)

        self.assertEqual(tag_filter.tags, ["work", "urgent"])
        self.assertTrue(tag_filter.match_all)

    def test_filter_default_match_all_is_false(self):
        """Test that match_all defaults to False (OR logic)."""
        tag_filter = TagFilter(tags=["work"])

        self.assertFalse(tag_filter.match_all)


if __name__ == "__main__":
    unittest.main()
