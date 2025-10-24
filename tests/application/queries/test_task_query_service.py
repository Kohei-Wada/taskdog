import os
import tempfile
import unittest
from datetime import datetime, timedelta

from application.queries.filters.today_filter import TodayFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestTaskQueryService(unittest.TestCase):
    """Test cases for TaskQueryService"""

    def setUp(self):
        """Create temporary file and initialize service for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
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
        today_filter = TodayFilter(include_completed=False)
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
        today_filter = TodayFilter(include_completed=False)
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
        today_filter = TodayFilter(include_completed=False)
        today_tasks = self.query_service.get_filtered_tasks(today_filter, sort_by="priority")

        # Verify sorted by priority (descending by default)
        self.assertEqual(len(today_tasks), 3)
        self.assertEqual(today_tasks[0].name, "High Priority")
        self.assertEqual(today_tasks[1].name, "Mid Priority")
        self.assertEqual(today_tasks[2].name, "Low Priority")

    def test_get_today_tasks_excludes_completed_by_default(self):
        """Test get_today_tasks excludes completed tasks by default"""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        today_filter = TodayFilter(include_completed=False)
        today_tasks = self.query_service.get_filtered_tasks(today_filter)

        self.assertEqual(len(today_tasks), 0)

    def test_get_today_tasks_includes_completed_when_specified(self):
        """Test get_today_tasks includes completed tasks when specified"""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_dt,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        today_filter = TodayFilter(include_completed=True)
        today_tasks = self.query_service.get_filtered_tasks(today_filter)

        self.assertEqual(len(today_tasks), 1)
        self.assertEqual(today_tasks[0].name, "Completed Today")


if __name__ == "__main__":
    unittest.main()
