"""Tests for ScheduleClearer."""

import os
import tempfile
import unittest
from datetime import datetime

from application.services.schedule_clearer import ScheduleClearer
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestScheduleClearer(unittest.TestCase):
    """Test cases for ScheduleClearer."""

    def setUp(self):
        """Create temporary file and initialize service for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.clearer = ScheduleClearer(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_clear_schedules_clears_all_schedule_fields(self):
        """Test clear_schedules clears each schedule field."""
        # Test data: (field_name, field_value, assertion_method)
        test_cases = [
            ("planned_start", datetime(2025, 1, 10, 9, 0), "assertIsNone"),
            ("planned_end", datetime(2025, 1, 15, 18, 0), "assertIsNone"),
            (
                "daily_allocations",
                {datetime(2025, 1, 10).date(): 4.0, datetime(2025, 1, 11).date(): 3.5},
                "assertEqual",
            ),
        ]

        for field_name, field_value, assertion_method in test_cases:
            with self.subTest(field=field_name):
                task = self.repository.create(name="Task 1", priority=1)
                setattr(task, field_name, field_value)
                self.repository.save(task)

                result = self.clearer.clear_schedules([task])

                if assertion_method == "assertIsNone":
                    self.assertIsNone(getattr(result[0], field_name))
                elif assertion_method == "assertEqual":
                    self.assertEqual(getattr(result[0], field_name), {})

    def test_clear_schedules_persists_changes(self):
        """Test clear_schedules saves changes to repository."""
        task = self.repository.create(name="Task 1", priority=1)
        task.planned_start = datetime(2025, 1, 10, 9, 0)
        task.planned_end = datetime(2025, 1, 15, 18, 0)
        task.daily_allocations = {datetime(2025, 1, 10).date(): 4.0}
        self.repository.save(task)

        tasks = [task]
        self.clearer.clear_schedules(tasks)

        # Retrieve from repository to verify persistence
        retrieved = self.repository.get_by_id(task.id)
        self.assertIsNone(retrieved.planned_start)
        self.assertIsNone(retrieved.planned_end)
        self.assertEqual(retrieved.daily_allocations, {})

    def test_clear_schedules_with_multiple_tasks(self):
        """Test clear_schedules handles multiple tasks."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task1.planned_start = datetime(2025, 1, 10, 9, 0)
        task1.daily_allocations = {datetime(2025, 1, 10).date(): 4.0}
        self.repository.save(task1)

        task2 = self.repository.create(name="Task 2", priority=2)
        task2.planned_end = datetime(2025, 1, 15, 18, 0)
        task2.daily_allocations = {datetime(2025, 1, 11).date(): 3.0}
        self.repository.save(task2)

        tasks = [task1, task2]
        result = self.clearer.clear_schedules(tasks)

        self.assertEqual(len(result), 2)
        self.assertIsNone(result[0].planned_start)
        self.assertEqual(result[0].daily_allocations, {})
        self.assertIsNone(result[1].planned_end)
        self.assertEqual(result[1].daily_allocations, {})

    def test_clear_schedules_with_empty_list(self):
        """Test clear_schedules with empty task list."""
        result = self.clearer.clear_schedules([])

        self.assertEqual(len(result), 0)

    def test_clear_schedules_does_not_affect_other_fields(self):
        """Test clear_schedules only clears schedule fields, not other fields."""
        task = self.repository.create(name="Task 1", priority=1)
        task.planned_start = datetime(2025, 1, 10, 9, 0)
        task.planned_end = datetime(2025, 1, 15, 18, 0)
        task.daily_allocations = {datetime(2025, 1, 10).date(): 4.0}
        task.deadline = datetime(2025, 1, 20, 18, 0)
        task.estimated_duration = 10.0
        self.repository.save(task)

        tasks = [task]
        result = self.clearer.clear_schedules(tasks)

        # Schedule fields cleared
        self.assertIsNone(result[0].planned_start)
        self.assertIsNone(result[0].planned_end)
        self.assertEqual(result[0].daily_allocations, {})

        # Other fields preserved
        self.assertEqual(result[0].name, "Task 1")
        self.assertEqual(result[0].priority, 1)
        self.assertIsNotNone(result[0].deadline)
        self.assertEqual(result[0].estimated_duration, 10.0)

    def test_clear_schedules_returns_tasks(self):
        """Test clear_schedules returns the tasks."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=2)

        tasks = [task1, task2]
        result = self.clearer.clear_schedules(tasks)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, task1.id)
        self.assertEqual(result[1].id, task2.id)

    def test_clear_schedules_with_task_already_cleared(self):
        """Test clear_schedules with task that has no schedule fields."""
        task = self.repository.create(name="Task 1", priority=1)
        # Don't set any schedule fields

        tasks = [task]
        result = self.clearer.clear_schedules(tasks)

        # Should not raise, just return task as-is
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0].planned_start)
        self.assertIsNone(result[0].planned_end)
        self.assertEqual(result[0].daily_allocations, {})


if __name__ == "__main__":
    unittest.main()
