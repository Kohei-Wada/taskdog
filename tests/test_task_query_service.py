import unittest
import tempfile
import os
from datetime import datetime, timedelta
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task, TaskStatus


class TestTaskQueryService(unittest.TestCase):
    """Test cases for TaskQueryService"""

    def setUp(self):
        """Create temporary file and initialize service for each test"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.query_service = TaskQueryService(self.repository)

        # Calculate date strings for testing
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)

        self.today_str = self.today.strftime("%Y-%m-%d 18:00:00")
        self.yesterday_str = self.yesterday.strftime("%Y-%m-%d 18:00:00")
        self.tomorrow_str = self.tomorrow.strftime("%Y-%m-%d 18:00:00")

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_get_today_tasks_returns_matching_tasks(self):
        """Test get_today_tasks returns tasks matching today's criteria"""
        # Create tasks
        task1 = Task(name="Deadline Today", priority=1, deadline=self.today_str)
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="In Progress", priority=1, status=TaskStatus.IN_PROGRESS)
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Not Today", priority=1, deadline=self.tomorrow_str)
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Query
        today_tasks = self.query_service.get_today_tasks(include_completed=False)

        # Verify
        self.assertEqual(len(today_tasks), 2)
        task_names = {t.name for t in today_tasks}
        self.assertIn("Deadline Today", task_names)
        self.assertIn("In Progress", task_names)
        self.assertNotIn("Not Today", task_names)

    def test_get_today_tasks_sorts_by_deadline(self):
        """Test get_today_tasks sorts tasks by deadline"""
        # Create tasks with different deadlines
        task1 = Task(name="Later", priority=1, id=1, deadline=self.tomorrow_str)
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(name="Earlier", priority=1, id=2, deadline=self.yesterday_str)
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(name="Today", priority=1, id=3, deadline=self.today_str)
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
        today_tasks = self.query_service.get_today_tasks(include_completed=False)

        # Verify sorted by deadline
        self.assertEqual(len(today_tasks), 3)
        self.assertEqual(today_tasks[0].name, "Earlier")
        self.assertEqual(today_tasks[1].name, "Today")
        self.assertEqual(today_tasks[2].name, "Later")

    def test_get_today_tasks_sorts_by_priority_when_deadline_same(self):
        """Test get_today_tasks sorts by priority when deadline is same"""
        # Create tasks with same deadline, different priorities
        task1 = Task(
            name="Low Priority", priority=1, id=1, deadline=self.today_str
        )
        task1.id = self.repository.generate_next_id()
        self.repository.save(task1)

        task2 = Task(
            name="High Priority", priority=5, id=2, deadline=self.today_str
        )
        task2.id = self.repository.generate_next_id()
        self.repository.save(task2)

        task3 = Task(
            name="Mid Priority", priority=3, id=3, deadline=self.today_str
        )
        task3.id = self.repository.generate_next_id()
        self.repository.save(task3)

        # Query
        today_tasks = self.query_service.get_today_tasks(include_completed=False)

        # Verify sorted by priority (descending)
        self.assertEqual(len(today_tasks), 3)
        self.assertEqual(today_tasks[0].name, "High Priority")
        self.assertEqual(today_tasks[1].name, "Mid Priority")
        self.assertEqual(today_tasks[2].name, "Low Priority")

    def test_get_today_tasks_excludes_completed_by_default(self):
        """Test get_today_tasks excludes completed tasks by default"""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_str,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        today_tasks = self.query_service.get_today_tasks(include_completed=False)

        self.assertEqual(len(today_tasks), 0)

    def test_get_today_tasks_includes_completed_when_specified(self):
        """Test get_today_tasks includes completed tasks when specified"""
        task = Task(
            name="Completed Today",
            priority=1,
            deadline=self.today_str,
            status=TaskStatus.COMPLETED,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        today_tasks = self.query_service.get_today_tasks(include_completed=True)

        self.assertEqual(len(today_tasks), 1)
        self.assertEqual(today_tasks[0].name, "Completed Today")

    def test_get_today_tasks_preserves_hierarchy(self):
        """Test get_today_tasks preserves task hierarchy"""
        # Create parent task not matching today's criteria
        parent = Task(name="Parent", priority=1, deadline=self.tomorrow_str)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child task matching today's criteria
        child = Task(
            name="Child", priority=1, deadline=self.today_str, parent_id=parent.id
        )
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        today_tasks = self.query_service.get_today_tasks(include_completed=False)

        # Both parent and child should be included
        self.assertEqual(len(today_tasks), 2)
        task_names = {t.name for t in today_tasks}
        self.assertIn("Parent", task_names)
        self.assertIn("Child", task_names)


if __name__ == "__main__":
    unittest.main()
