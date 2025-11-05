import os
import tempfile
import unittest
from datetime import datetime, timedelta

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.filters.today_filter import TodayFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.database.sqlite_task_repository import SqliteTaskRepository


class TestTaskQueryService(unittest.TestCase):
    """Test cases for TaskQueryService"""

    def setUp(self):
        """Create temporary file and initialize service for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = SqliteTaskRepository(f"sqlite:///{self.test_filename}")
        self.query_service = TaskQueryService(self.repository)

        # Calculate date strings for testing
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)

        self.today_dt = datetime.combine(self.today, datetime.min.time()).replace(hour=18)
        self.yesterday_dt = datetime.combine(self.yesterday, datetime.min.time()).replace(hour=18)
        self.tomorrow_dt = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=18)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if hasattr(self, "repository") and hasattr(self.repository, "close"):
            self.repository.close()
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_get_today_tasks_returns_matching_tasks(self):
        """Test get_today_tasks returns tasks matching today's criteria"""
        # Create tasks
        task1 = Task(name="Deadline Today", priority=1, deadline=self.today_dt)
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="In Progress", priority=1, status=TaskStatus.IN_PROGRESS)
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Not Today", priority=1, deadline=self.tomorrow_dt)
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Query
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(today_filter)

        # Verify
        self.assertEqual(len(today_tasks), 2)
        task_names = {t.name for t in today_tasks}
        self.assertIn("Deadline Today", task_names)
        self.assertIn("In Progress", task_names)
        self.assertNotIn("Not Today", task_names)

    def test_get_today_tasks_sorts_by_deadline(self):
        """Test get_today_tasks sorts tasks by deadline"""
        # Create tasks with different deadlines
        task1 = Task(name="Later", priority=1, id=1, deadline=self.tomorrow_dt)
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Earlier", priority=1, id=2, deadline=self.yesterday_dt)
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Today", priority=1, id=3, deadline=self.today_dt)
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Make all tasks "today tasks" by setting IN_PROGRESS
        task1.status = TaskStatus.IN_PROGRESS
        task2.status = TaskStatus.IN_PROGRESS
        task3.status = TaskStatus.IN_PROGRESS
        self.repository.save(task1)
        self.repository.save(task2)
        self.repository.save(task3)

        # Query
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(today_filter, sort_by="deadline")

        # Verify sorted by deadline
        self.assertEqual(len(today_tasks), 3)
        self.assertEqual(today_tasks[0].name, "Earlier")
        self.assertEqual(today_tasks[1].name, "Today")
        self.assertEqual(today_tasks[2].name, "Later")

    def test_get_today_tasks_sorts_by_priority_when_specified(self):
        """Test get_today_tasks can sort by priority when specified"""
        # Create tasks with same deadline, different priorities
        task1 = Task(name="Low Priority", priority=1, id=1, deadline=self.today_dt)
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="High Priority", priority=5, id=2, deadline=self.today_dt)
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Mid Priority", priority=3, id=3, deadline=self.today_dt)
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Query with priority sorting
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(today_filter, sort_by="priority")

        # Verify sorted by priority (descending by default)
        self.assertEqual(len(today_tasks), 3)
        self.assertEqual(today_tasks[0].name, "High Priority")
        self.assertEqual(today_tasks[1].name, "Mid Priority")
        self.assertEqual(today_tasks[2].name, "Low Priority")

    def test_composite_filter_with_incomplete_excludes_completed(self):
        """Test CompositeFilter with IncompleteFilter excludes completed tasks"""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # This mimics 'taskdog today' default behavior
        composite_filter = CompositeFilter([IncompleteFilter(), TodayFilter()])
        today_tasks = self.query_service.get_filtered_tasks(composite_filter)

        self.assertEqual(len(today_tasks), 0)

    def test_today_filter_alone_includes_completed(self):
        """Test TodayFilter alone includes completed tasks (mimics 'taskdog today --all')"""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # This mimics 'taskdog today --all' behavior
        today_filter = TodayFilter()
        today_tasks = self.query_service.get_filtered_tasks(today_filter)

        self.assertEqual(len(today_tasks), 1)
        self.assertEqual(today_tasks[0].name, "Completed Today")

    def test_filter_by_tags_with_or_logic(self):
        """Test filter_by_tags with OR logic returns tasks with any specified tag."""
        # Create tasks with different tags
        task1 = Task(name="Work Task", priority=1, tags=["work", "urgent"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Personal Task", priority=1, tags=["personal"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Client Task", priority=1, tags=["work", "client-a"])
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        task4 = Task(name="No Tags", priority=1, tags=[])
        task4.id = self.repository.generate_next_id()
        self.repository.save(task4)

        # Query with OR logic (default)
        result = self.query_service.filter_by_tags(["work", "personal"], match_all=False)

        # Should return tasks 1, 2, and 3 (all have either "work" or "personal")
        self.assertEqual(len(result), 3)
        task_names = {t.name for t in result}
        self.assertIn("Work Task", task_names)
        self.assertIn("Personal Task", task_names)
        self.assertIn("Client Task", task_names)
        self.assertNotIn("No Tags", task_names)

    def test_filter_by_tags_with_and_logic(self):
        """Test filter_by_tags with AND logic returns tasks with all specified tags."""
        # Create tasks with different tag combinations
        task1 = Task(name="Work and Urgent", priority=1, tags=["work", "urgent"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Only Work", priority=1, tags=["work"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Work and Client", priority=1, tags=["work", "urgent", "client-a"])
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Query with AND logic
        result = self.query_service.filter_by_tags(["work", "urgent"], match_all=True)

        # Should return only tasks 1 and 3 (both have "work" AND "urgent")
        self.assertEqual(len(result), 2)
        task_names = {t.name for t in result}
        self.assertIn("Work and Urgent", task_names)
        self.assertIn("Work and Client", task_names)
        self.assertNotIn("Only Work", task_names)

    def test_filter_by_tags_with_empty_list_returns_all(self):
        """Test filter_by_tags with empty tag list returns all tasks."""
        task1 = Task(name="Task 1", priority=1, tags=["work"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Task 2", priority=1, tags=[])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        result = self.query_service.filter_by_tags([], match_all=False)

        self.assertEqual(len(result), 2)

    def test_filter_by_tags_with_nonexistent_tag(self):
        """Test filter_by_tags with nonexistent tag returns empty list."""
        task1 = Task(name="Task 1", priority=1, tags=["work"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        result = self.query_service.filter_by_tags(["nonexistent"], match_all=False)

        self.assertEqual(len(result), 0)

    def test_get_all_tags_returns_tag_counts(self):
        """Test get_all_tags returns all unique tags with their counts."""
        # Create tasks with various tags
        task1 = Task(name="Task 1", priority=1, tags=["work", "urgent"])
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Task 2", priority=1, tags=["work", "client-a"])
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Task 3", priority=1, tags=["personal"])
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        task4 = Task(name="Task 4", priority=1, tags=[])
        task4.id = self.repository.generate_next_id()
        self.repository.save(task4)

        # Get all tags
        result = self.query_service.get_all_tags()

        # Verify counts
        self.assertEqual(len(result), 4)
        self.assertEqual(result["work"], 2)
        self.assertEqual(result["urgent"], 1)
        self.assertEqual(result["client-a"], 1)
        self.assertEqual(result["personal"], 1)

    def test_get_all_tags_with_no_tasks_returns_empty(self):
        """Test get_all_tags with no tasks returns empty dict."""
        result = self.query_service.get_all_tags()

        self.assertEqual(result, {})

    def test_get_all_tags_with_no_tags_returns_empty(self):
        """Test get_all_tags with tasks but no tags returns empty dict."""
        task = Task(name="Task", priority=1, tags=[])
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        result = self.query_service.get_all_tags()

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
