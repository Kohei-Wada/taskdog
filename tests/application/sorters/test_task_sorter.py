import unittest
from datetime import datetime, timedelta

from application.sorters.task_sorter import TaskSorter
from domain.entities.task import Task, TaskStatus


class TestTaskSorter(unittest.TestCase):
    """Test cases for TaskSorter"""

    def setUp(self):
        """Initialize sorter for each test"""
        self.sorter = TaskSorter()

        # Calculate date strings for testing
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        self.today_str = today.strftime("%Y-%m-%d 18:00:00")
        self.yesterday_str = yesterday.strftime("%Y-%m-%d 18:00:00")
        self.tomorrow_str = tomorrow.strftime("%Y-%m-%d 18:00:00")

    def test_sort_by_id_ascending(self):
        """Test sorting by ID in ascending order"""
        task1 = Task(name="Task 3", priority=1)
        task1.id = 3
        task2 = Task(name="Task 1", priority=1)
        task2.id = 1
        task3 = Task(name="Task 2", priority=1)
        task3.id = 2

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="id")

        self.assertEqual(sorted_tasks[0].id, 1)
        self.assertEqual(sorted_tasks[1].id, 2)
        self.assertEqual(sorted_tasks[2].id, 3)

    def test_sort_by_id_descending(self):
        """Test sorting by ID in descending order"""
        task1 = Task(name="Task 3", priority=1)
        task1.id = 3
        task2 = Task(name="Task 1", priority=1)
        task2.id = 1
        task3 = Task(name="Task 2", priority=1)
        task3.id = 2

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="id", reverse=True)

        self.assertEqual(sorted_tasks[0].id, 3)
        self.assertEqual(sorted_tasks[1].id, 2)
        self.assertEqual(sorted_tasks[2].id, 1)

    def test_sort_by_priority_descending_default(self):
        """Test sorting by priority in descending order (default)"""
        task1 = Task(name="Low Priority", priority=1)
        task1.id = 1
        task2 = Task(name="High Priority", priority=5)
        task2.id = 2
        task3 = Task(name="Medium Priority", priority=3)
        task3.id = 3

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="priority")

        # Default for priority is descending (higher priority first)
        self.assertEqual(sorted_tasks[0].priority, 5)
        self.assertEqual(sorted_tasks[1].priority, 3)
        self.assertEqual(sorted_tasks[2].priority, 1)

    def test_sort_by_priority_ascending(self):
        """Test sorting by priority in ascending order"""
        task1 = Task(name="Low Priority", priority=1)
        task1.id = 1
        task2 = Task(name="High Priority", priority=5)
        task2.id = 2
        task3 = Task(name="Medium Priority", priority=3)
        task3.id = 3

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="priority", reverse=True)

        # Reverse=True for priority means ascending
        self.assertEqual(sorted_tasks[0].priority, 1)
        self.assertEqual(sorted_tasks[1].priority, 3)
        self.assertEqual(sorted_tasks[2].priority, 5)

    def test_sort_by_deadline_ascending(self):
        """Test sorting by deadline in ascending order"""
        task1 = Task(name="Tomorrow", priority=1, deadline=self.tomorrow_str)
        task1.id = 1
        task2 = Task(name="Yesterday", priority=1, deadline=self.yesterday_str)
        task2.id = 2
        task3 = Task(name="Today", priority=1, deadline=self.today_str)
        task3.id = 3

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="deadline")

        self.assertEqual(sorted_tasks[0].name, "Yesterday")
        self.assertEqual(sorted_tasks[1].name, "Today")
        self.assertEqual(sorted_tasks[2].name, "Tomorrow")

    def test_sort_by_deadline_none_values_last(self):
        """Test that tasks with no deadline are sorted last"""
        task1 = Task(name="No Deadline", priority=1, deadline=None)
        task1.id = 1
        task2 = Task(name="With Deadline", priority=1, deadline=self.today_str)
        task2.id = 2

        tasks = [task1, task2]
        sorted_tasks = self.sorter.sort(tasks, sort_by="deadline")

        self.assertEqual(sorted_tasks[0].name, "With Deadline")
        self.assertEqual(sorted_tasks[1].name, "No Deadline")

    def test_sort_by_name_alphabetical(self):
        """Test sorting by name alphabetically"""
        task1 = Task(name="Zebra", priority=1)
        task1.id = 1
        task2 = Task(name="Apple", priority=1)
        task2.id = 2
        task3 = Task(name="Banana", priority=1)
        task3.id = 3

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="name")

        self.assertEqual(sorted_tasks[0].name, "Apple")
        self.assertEqual(sorted_tasks[1].name, "Banana")
        self.assertEqual(sorted_tasks[2].name, "Zebra")

    def test_sort_by_name_case_insensitive(self):
        """Test that name sorting is case-insensitive"""
        task1 = Task(name="zebra", priority=1)
        task1.id = 1
        task2 = Task(name="Apple", priority=1)
        task2.id = 2
        task3 = Task(name="BANANA", priority=1)
        task3.id = 3

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="name")

        self.assertEqual(sorted_tasks[0].name, "Apple")
        self.assertEqual(sorted_tasks[1].name, "BANANA")
        self.assertEqual(sorted_tasks[2].name, "zebra")

    def test_sort_by_status(self):
        """Test sorting by status"""
        task1 = Task(name="Task 1", priority=1, status=TaskStatus.PENDING)
        task1.id = 1
        task2 = Task(name="Task 2", priority=1, status=TaskStatus.COMPLETED)
        task2.id = 2
        task3 = Task(name="Task 3", priority=1, status=TaskStatus.IN_PROGRESS)
        task3.id = 3

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="status")

        # Alphabetical by status value: COMPLETED, IN_PROGRESS, PENDING
        self.assertEqual(sorted_tasks[0].status, TaskStatus.COMPLETED)
        self.assertEqual(sorted_tasks[1].status, TaskStatus.IN_PROGRESS)
        self.assertEqual(sorted_tasks[2].status, TaskStatus.PENDING)

    def test_sort_by_planned_start(self):
        """Test sorting by planned start date"""
        task1 = Task(name="Start Tomorrow", priority=1, planned_start=self.tomorrow_str)
        task1.id = 1
        task2 = Task(name="Start Yesterday", priority=1, planned_start=self.yesterday_str)
        task2.id = 2
        task3 = Task(name="Start Today", priority=1, planned_start=self.today_str)
        task3.id = 3

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by="planned_start")

        self.assertEqual(sorted_tasks[0].name, "Start Yesterday")
        self.assertEqual(sorted_tasks[1].name, "Start Today")
        self.assertEqual(sorted_tasks[2].name, "Start Tomorrow")

    def test_sort_by_planned_start_none_values_last(self):
        """Test that tasks with no planned_start are sorted last"""
        task1 = Task(name="No Plan", priority=1, planned_start=None)
        task1.id = 1
        task2 = Task(name="With Plan", priority=1, planned_start=self.today_str)
        task2.id = 2

        tasks = [task1, task2]
        sorted_tasks = self.sorter.sort(tasks, sort_by="planned_start")

        self.assertEqual(sorted_tasks[0].name, "With Plan")
        self.assertEqual(sorted_tasks[1].name, "No Plan")

    def test_sort_invalid_key_raises_error(self):
        """Test that invalid sort key raises ValueError"""
        task = Task(name="Task", priority=1)
        task.id = 1
        tasks = [task]

        with self.assertRaises(ValueError) as context:
            self.sorter.sort(tasks, sort_by="invalid_key")

        self.assertIn("Invalid sort_by", str(context.exception))

    def test_sort_empty_list(self):
        """Test sorting an empty list"""
        tasks = []
        sorted_tasks = self.sorter.sort(tasks, sort_by="id")

        self.assertEqual(len(sorted_tasks), 0)


if __name__ == "__main__":
    unittest.main()
