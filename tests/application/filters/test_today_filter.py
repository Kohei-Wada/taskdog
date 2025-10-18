import os
import tempfile
import unittest
from datetime import datetime, timedelta

from application.queries.filters.today_filter import TodayFilter
from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestTodayFilter(unittest.TestCase):
    """Test cases for TodayFilter"""

    def setUp(self):
        """Create temporary file and initialize repository for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)

        # Calculate date strings for testing
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)

        # Helper methods to create datetime strings
        self.today_str = self.today.strftime("%Y-%m-%d 18:00:00")
        self.yesterday_str = self.yesterday.strftime("%Y-%m-%d 18:00:00")
        self.tomorrow_str = self.tomorrow.strftime("%Y-%m-%d 18:00:00")

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_filter_includes_deadline_today(self):
        """Test filter includes task with deadline today"""
        task = Task(name="Deadline Today", priority=1, deadline=self.today_str)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter(include_completed=False)
        filtered = filter_obj.filter(tasks)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "Deadline Today")

    def test_filter_excludes_deadline_tomorrow(self):
        """Test filter excludes task with deadline tomorrow"""
        task = Task(name="Deadline Tomorrow", priority=1, deadline=self.tomorrow_str)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter(include_completed=False)
        filtered = filter_obj.filter(tasks)

        self.assertEqual(len(filtered), 0)

    def test_filter_includes_in_progress_task(self):
        """Test filter includes IN_PROGRESS task"""
        task = Task(name="In Progress", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter(include_completed=False)
        filtered = filter_obj.filter(tasks)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "In Progress")

    def test_filter_includes_planned_period_today(self):
        """Test filter includes task with planned period including today"""
        task = Task(
            name="Planned Today",
            priority=1,
            planned_start=self.yesterday_str,
            planned_end=self.tomorrow_str,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter(include_completed=False)
        filtered = filter_obj.filter(tasks)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "Planned Today")

    def test_filter_excludes_completed_by_default(self):
        """Test filter excludes completed tasks by default"""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_str,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter(include_completed=False)
        filtered = filter_obj.filter(tasks)

        self.assertEqual(len(filtered), 0)

    def test_filter_includes_completed_when_specified(self):
        """Test filter includes completed tasks when specified"""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_str,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        tasks = self.repository.get_all()
        filter_obj = TodayFilter(include_completed=True)
        filtered = filter_obj.filter(tasks)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "Completed Today")


if __name__ == "__main__":
    unittest.main()
