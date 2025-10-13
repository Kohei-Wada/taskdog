"""Tests for SchedulePropagator."""

import os
import tempfile
import unittest

from application.services.schedule_propagator import SchedulePropagator
from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestSchedulePropagator(unittest.TestCase):
    """Test cases for SchedulePropagator."""

    def setUp(self):
        """Create temporary file and initialize propagator for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.propagator = SchedulePropagator(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_propagate_periods_updates_parent_to_encompass_children(self):
        """Test that parent's period encompasses all children's periods."""
        # Create parent
        parent = Task(name="Parent", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create children with schedules
        child1 = Task(
            name="Child 1",
            priority=1,
            parent_id=parent.id,
            planned_start="2025-10-20 09:00:00",
            planned_end="2025-10-22 18:00:00",
        )
        child1.id = self.repository.generate_next_id()
        self.repository.save(child1)

        child2 = Task(
            name="Child 2",
            priority=1,
            parent_id=parent.id,
            planned_start="2025-10-21 09:00:00",
            planned_end="2025-10-24 18:00:00",
        )
        child2.id = self.repository.generate_next_id()
        self.repository.save(child2)

        # Propagate
        all_tasks = [parent, child1, child2]
        updated_tasks = [child1, child2]
        modified_tasks = self.propagator.propagate_periods(all_tasks, updated_tasks)

        # Verify parent is in modified tasks
        parent_modified = next((t for t in modified_tasks if t.id == parent.id), None)
        self.assertIsNotNone(parent_modified)

        # Verify parent's period encompasses all children
        self.assertEqual(parent_modified.planned_start, "2025-10-20 09:00:00")  # min start
        self.assertEqual(parent_modified.planned_end, "2025-10-24 18:00:00")  # max end

    def test_propagate_periods_updates_grandparent_recursively(self):
        """Test that propagation updates grandparent recursively."""
        # Create grandparent
        grandparent = Task(name="Grandparent", priority=1)
        grandparent.id = self.repository.generate_next_id()
        self.repository.save(grandparent)

        # Create parent as child of grandparent
        parent = Task(name="Parent", priority=1, parent_id=grandparent.id)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child with schedule
        child = Task(
            name="Child",
            priority=1,
            parent_id=parent.id,
            planned_start="2025-10-20 09:00:00",
            planned_end="2025-10-24 18:00:00",
        )
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Propagate
        all_tasks = [grandparent, parent, child]
        updated_tasks = [child]
        modified_tasks = self.propagator.propagate_periods(all_tasks, updated_tasks)

        # Verify parent is updated
        parent_modified = next((t for t in modified_tasks if t.id == parent.id), None)
        self.assertIsNotNone(parent_modified)
        self.assertEqual(parent_modified.planned_start, "2025-10-20 09:00:00")
        self.assertEqual(parent_modified.planned_end, "2025-10-24 18:00:00")

        # Verify grandparent is also updated
        grandparent_modified = next((t for t in modified_tasks if t.id == grandparent.id), None)
        self.assertIsNotNone(grandparent_modified)
        self.assertEqual(grandparent_modified.planned_start, "2025-10-20 09:00:00")
        self.assertEqual(grandparent_modified.planned_end, "2025-10-24 18:00:00")

    def test_propagate_periods_skips_archived_parent(self):
        """Test that propagation skips archived parent tasks."""
        # Create archived parent
        parent = Task(name="Parent", priority=1, status=TaskStatus.ARCHIVED)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child with schedule
        child = Task(
            name="Child",
            priority=1,
            parent_id=parent.id,
            planned_start="2025-10-20 09:00:00",
            planned_end="2025-10-24 18:00:00",
        )
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Propagate
        all_tasks = [parent, child]
        updated_tasks = [child]
        modified_tasks = self.propagator.propagate_periods(all_tasks, updated_tasks)

        # Verify only child is in modified tasks (parent not updated)
        self.assertEqual(len(modified_tasks), 1)
        self.assertEqual(modified_tasks[0].id, child.id)

    def test_propagate_periods_ignores_children_without_schedules(self):
        """Test that propagation ignores children without schedules."""
        # Create parent
        parent = Task(name="Parent", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child with schedule
        child1 = Task(
            name="Child 1",
            priority=1,
            parent_id=parent.id,
            planned_start="2025-10-20 09:00:00",
            planned_end="2025-10-22 18:00:00",
        )
        child1.id = self.repository.generate_next_id()
        self.repository.save(child1)

        # Create child without schedule
        child2 = Task(name="Child 2", priority=1, parent_id=parent.id)
        child2.id = self.repository.generate_next_id()
        self.repository.save(child2)

        # Propagate
        all_tasks = [parent, child1, child2]
        updated_tasks = [child1]
        modified_tasks = self.propagator.propagate_periods(all_tasks, updated_tasks)

        # Verify parent uses only child1's schedule
        parent_modified = next((t for t in modified_tasks if t.id == parent.id), None)
        self.assertIsNotNone(parent_modified)
        self.assertEqual(parent_modified.planned_start, "2025-10-20 09:00:00")
        self.assertEqual(parent_modified.planned_end, "2025-10-22 18:00:00")

    def test_clear_unscheduled_tasks_clears_old_schedules(self):
        """Test that clear_unscheduled_tasks removes old schedules from unscheduled tasks."""
        # Create tasks with schedules
        task1 = Task(
            name="Task 1",
            priority=1,
            estimated_duration=5.0,
            planned_start="2025-10-20 09:00:00",
            planned_end="2025-10-22 18:00:00",
        )
        task1.id = self.repository.generate_next_id()
        task1.daily_allocations = {"2025-10-20": 3.0, "2025-10-21": 2.0}
        self.repository.save(task1)

        task2 = Task(
            name="Task 2",
            priority=1,
            estimated_duration=5.0,
            planned_start="2025-10-23 09:00:00",
            planned_end="2025-10-24 18:00:00",
        )
        task2.id = self.repository.generate_next_id()
        task2.daily_allocations = {"2025-10-23": 3.0, "2025-10-24": 2.0}
        self.repository.save(task2)

        # Only task2 was successfully rescheduled
        all_tasks = [task1, task2]
        updated_tasks = [task2]
        result = self.propagator.clear_unscheduled_tasks(all_tasks, updated_tasks)

        # Verify result contains both tasks
        self.assertEqual(len(result), 2)

        # Verify task1's schedule was cleared
        task1_result = next((t for t in result if t.id == task1.id), None)
        self.assertIsNotNone(task1_result)
        self.assertIsNone(task1_result.planned_start)
        self.assertIsNone(task1_result.planned_end)
        self.assertEqual(task1_result.daily_allocations, {})

        # Verify task2's schedule is unchanged
        task2_result = next((t for t in result if t.id == task2.id), None)
        self.assertIsNotNone(task2_result)
        self.assertEqual(task2_result.planned_start, "2025-10-23 09:00:00")

    def test_clear_unscheduled_tasks_skips_completed_tasks(self):
        """Test that clear_unscheduled_tasks skips completed tasks."""
        # Create completed task with schedule
        task = Task(
            name="Completed Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            estimated_duration=5.0,
            planned_start="2025-10-20 09:00:00",
            planned_end="2025-10-22 18:00:00",
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # No updated tasks
        all_tasks = [task]
        updated_tasks = []
        result = self.propagator.clear_unscheduled_tasks(all_tasks, updated_tasks)

        # Verify completed task is not in result (not cleared)
        self.assertEqual(len(result), 0)

    def test_clear_unscheduled_tasks_skips_parent_tasks(self):
        """Test that clear_unscheduled_tasks skips parent tasks."""
        # Create parent with schedule
        parent = Task(
            name="Parent",
            priority=1,
            estimated_duration=10.0,
            planned_start="2025-10-20 09:00:00",
            planned_end="2025-10-24 18:00:00",
        )
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child
        child = Task(name="Child", priority=1, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # No updated tasks
        all_tasks = [parent, child]
        updated_tasks = []
        result = self.propagator.clear_unscheduled_tasks(all_tasks, updated_tasks)

        # Verify parent is not in result (parent tasks are skipped)
        self.assertEqual(len(result), 0)

    def test_clear_unscheduled_tasks_skips_never_scheduled_tasks(self):
        """Test that clear_unscheduled_tasks skips tasks that never had schedules."""
        # Create task without schedule
        task = Task(name="Never Scheduled", priority=1, estimated_duration=5.0)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # No updated tasks
        all_tasks = [task]
        updated_tasks = []
        result = self.propagator.clear_unscheduled_tasks(all_tasks, updated_tasks)

        # Verify task is not in result (never had schedule)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
