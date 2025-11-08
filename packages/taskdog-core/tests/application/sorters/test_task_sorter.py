import unittest
from datetime import datetime, timedelta

from parameterized import parameterized

from taskdog_core.application.sorters.task_sorter import TaskSorter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskSorter(unittest.TestCase):
    """Test cases for TaskSorter"""

    def setUp(self):
        """Initialize sorter for each test"""
        self.sorter = TaskSorter()

        # Calculate datetimes for testing
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        self.today_str = datetime.combine(today, datetime.min.time()).replace(hour=18)
        self.yesterday_str = datetime.combine(yesterday, datetime.min.time()).replace(
            hour=18
        )
        self.tomorrow_str = datetime.combine(tomorrow, datetime.min.time()).replace(
            hour=18
        )

    @parameterized.expand(
        [
            # (field, reverse, task_values, expected_order, attr_to_check)
            ("id", False, [3, 1, 2], [1, 2, 3], "id"),
            ("id", True, [3, 1, 2], [3, 2, 1], "id"),
            ("priority", False, [1, 5, 3], [5, 3, 1], "priority"),  # Default descending
            (
                "priority",
                True,
                [1, 5, 3],
                [1, 3, 5],
                "priority",
            ),  # Reverse to ascending
        ]
    )
    def test_sort_by_id_and_priority(
        self, field, reverse, task_values, expected_order, attr_to_check
    ):
        """Test sorting by ID and priority with different directions."""
        tasks = []
        for i, value in enumerate(task_values, 1):
            if field == "id":
                task = Task(name=f"Task {value}", priority=1)
                task.id = value
            else:  # priority
                task = Task(name=f"Task {i}", priority=value)
                task.id = i
            tasks.append(task)

        sorted_tasks = self.sorter.sort(tasks, sort_by=field, reverse=reverse)

        for i, expected in enumerate(expected_order):
            self.assertEqual(getattr(sorted_tasks[i], attr_to_check), expected)

    @parameterized.expand(
        [
            ("deadline", ["Yesterday", "Today", "Tomorrow"]),
            ("planned_start", ["Start Yesterday", "Start Today", "Start Tomorrow"]),
        ]
    )
    def test_sort_by_date_fields(self, field, expected_names):
        """Test sorting by date fields (deadline, planned_start)."""
        task1 = Task(name=expected_names[2], priority=1, **{field: self.tomorrow_str})
        task1.id = 1
        task2 = Task(name=expected_names[0], priority=1, **{field: self.yesterday_str})
        task2.id = 2
        task3 = Task(name=expected_names[1], priority=1, **{field: self.today_str})
        task3.id = 3

        tasks = [task1, task2, task3]
        sorted_tasks = self.sorter.sort(tasks, sort_by=field)

        for i, expected_name in enumerate(expected_names):
            self.assertEqual(sorted_tasks[i].name, expected_name)

    @parameterized.expand(
        [
            ("deadline", "No Deadline", "With Deadline"),
            ("planned_start", "No Plan", "With Plan"),
        ]
    )
    def test_sort_with_none_values_last(self, field, none_name, value_name):
        """Test that tasks with None date values are sorted last."""
        task1 = Task(name=none_name, priority=1, **{field: None})
        task1.id = 1
        task2 = Task(name=value_name, priority=1, **{field: self.today_str})
        task2.id = 2

        tasks = [task1, task2]
        sorted_tasks = self.sorter.sort(tasks, sort_by=field)

        self.assertEqual(sorted_tasks[0].name, value_name)
        self.assertEqual(sorted_tasks[1].name, none_name)

    @parameterized.expand(
        [
            (
                "alphabetical",
                ["Zebra", "Apple", "Banana"],
                ["Apple", "Banana", "Zebra"],
            ),
            (
                "case_insensitive",
                ["zebra", "Apple", "BANANA"],
                ["Apple", "BANANA", "zebra"],
            ),
        ]
    )
    def test_sort_by_name(self, scenario, input_names, expected_names):
        """Test sorting by name (alphabetical and case-insensitive)."""
        tasks = []
        for i, name in enumerate(input_names, 1):
            task = Task(name=name, priority=1)
            task.id = i
            tasks.append(task)

        sorted_tasks = self.sorter.sort(tasks, sort_by="name")

        for i, expected_name in enumerate(expected_names):
            self.assertEqual(sorted_tasks[i].name, expected_name)

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
