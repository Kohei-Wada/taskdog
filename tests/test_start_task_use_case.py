import contextlib
import os
import tempfile
import unittest

from application.dto.start_task_input import StartTaskInput
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskWithChildrenError,
)
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestStartTaskUseCase(unittest.TestCase):
    """Test cases for StartTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = StartTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_sets_status_to_in_progress(self):
        """Test execute sets task status to IN_PROGRESS"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)

    def test_execute_records_actual_start_time(self):
        """Test execute records actual start timestamp"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNotNone(result.actual_start)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(retrieved.actual_start)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = StartTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_does_not_update_actual_end(self):
        """Test execute does not set actual_end when starting"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNone(result.actual_end)

    def test_execute_auto_starts_pending_parent_task(self):
        """Test execute auto-starts parent task if it's PENDING"""
        # Create parent task
        parent = Task(name="Parent Task", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child task
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start child task
        input_dto = StartTaskInput(task_id=child.id)
        self.use_case.execute(input_dto)

        # Verify parent is now IN_PROGRESS
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(parent_updated.actual_start)

    def test_execute_does_not_change_in_progress_parent(self):
        """Test execute does not change parent that's already IN_PROGRESS"""
        # Create parent task with IN_PROGRESS status
        parent = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        parent.id = self.repository.generate_next_id()
        parent.actual_start = "2024-01-01 10:00:00"
        self.repository.save(parent)

        # Create child task
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start child task
        input_dto = StartTaskInput(task_id=child.id)
        self.use_case.execute(input_dto)

        # Verify parent status and actual_start remain unchanged
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(parent_updated.actual_start, "2024-01-01 10:00:00")

    def test_execute_does_not_change_completed_parent(self):
        """Test execute does not change parent that's COMPLETED"""
        # Create parent task with COMPLETED status
        parent = Task(name="Parent Task", priority=1, status=TaskStatus.COMPLETED)
        parent.id = self.repository.generate_next_id()
        parent.actual_start = "2024-01-01 10:00:00"
        parent.actual_end = "2024-01-01 12:00:00"
        self.repository.save(parent)

        # Create child task
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start child task
        input_dto = StartTaskInput(task_id=child.id)
        self.use_case.execute(input_dto)

        # Verify parent status remains COMPLETED
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.status, TaskStatus.COMPLETED)

    def test_execute_without_parent_works_normally(self):
        """Test execute works normally for tasks without parent"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(result.actual_start)

    def test_execute_auto_starts_all_ancestor_tasks(self):
        """Test execute auto-starts all ancestor tasks (grandparent and beyond)"""
        # Create grandparent task (PENDING)
        grandparent = Task(name="Grandparent Task", priority=1)
        grandparent.id = self.repository.generate_next_id()
        self.repository.save(grandparent)

        # Create parent task (PENDING)
        parent = Task(name="Parent Task", priority=1, parent_id=grandparent.id)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child task (PENDING)
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start child task
        input_dto = StartTaskInput(task_id=child.id)
        self.use_case.execute(input_dto)

        # Verify child is IN_PROGRESS
        child_updated = self.repository.get_by_id(child.id)
        self.assertEqual(child_updated.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(child_updated.actual_start)

        # Verify parent is IN_PROGRESS
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(parent_updated.actual_start)

        # Verify grandparent is also IN_PROGRESS
        grandparent_updated = self.repository.get_by_id(grandparent.id)
        self.assertEqual(grandparent_updated.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(grandparent_updated.actual_start)

    def test_execute_skips_non_pending_ancestors(self):
        """Test execute skips ancestors that are not PENDING"""
        # Create grandparent task (IN_PROGRESS)
        grandparent = Task(name="Grandparent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        grandparent.id = self.repository.generate_next_id()
        grandparent.actual_start = "2024-01-01 09:00:00"
        self.repository.save(grandparent)

        # Create parent task (PENDING)
        parent = Task(name="Parent Task", priority=1, parent_id=grandparent.id)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child task (PENDING)
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start child task
        input_dto = StartTaskInput(task_id=child.id)
        self.use_case.execute(input_dto)

        # Verify parent is IN_PROGRESS
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.status, TaskStatus.IN_PROGRESS)

        # Verify grandparent status and timestamp remain unchanged
        grandparent_updated = self.repository.get_by_id(grandparent.id)
        self.assertEqual(grandparent_updated.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(grandparent_updated.actual_start, "2024-01-01 09:00:00")

    def test_execute_raises_error_when_task_has_children(self):
        """Test execute raises TaskWithChildrenError when starting a parent task"""
        # Create parent task
        parent = Task(name="Parent Task", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child task
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Try to start parent task - should raise error
        input_dto = StartTaskInput(task_id=parent.id)

        with self.assertRaises(TaskWithChildrenError) as context:
            self.use_case.execute(input_dto)

        # Verify error details
        self.assertEqual(context.exception.task_id, parent.id)
        self.assertEqual(len(context.exception.children), 1)
        self.assertEqual(context.exception.children[0].id, child.id)

    def test_execute_raises_error_when_task_has_multiple_children(self):
        """Test execute raises TaskWithChildrenError with multiple children"""
        # Create parent task
        parent = Task(name="Parent Task", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create multiple child tasks
        child1 = Task(name="Child Task 1", priority=2, parent_id=parent.id)
        child1.id = self.repository.generate_next_id()
        self.repository.save(child1)

        child2 = Task(name="Child Task 2", priority=3, parent_id=parent.id)
        child2.id = self.repository.generate_next_id()
        self.repository.save(child2)

        child3 = Task(name="Child Task 3", priority=4, parent_id=parent.id)
        child3.id = self.repository.generate_next_id()
        self.repository.save(child3)

        # Try to start parent task - should raise error
        input_dto = StartTaskInput(task_id=parent.id)

        with self.assertRaises(TaskWithChildrenError) as context:
            self.use_case.execute(input_dto)

        # Verify error details
        self.assertEqual(context.exception.task_id, parent.id)
        self.assertEqual(len(context.exception.children), 3)

    def test_execute_allows_leaf_task_to_start(self):
        """Test execute allows leaf tasks (without children) to start normally"""
        # Create parent task
        parent = Task(name="Parent Task", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create leaf child task
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start leaf child task - should succeed
        input_dto = StartTaskInput(task_id=child.id)
        result = self.use_case.execute(input_dto)

        # Verify child is IN_PROGRESS
        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(result.actual_start)

    def test_execute_raises_error_when_starting_completed_task(self):
        """Test execute raises TaskAlreadyFinishedError when starting COMPLETED task"""
        # Create and complete a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        task.actual_start = "2024-01-01 10:00:00"
        task.actual_end = "2024-01-01 12:00:00"
        self.repository.save(task)

        # Try to start the completed task - should raise error
        input_dto = StartTaskInput(task_id=task.id)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.use_case.execute(input_dto)

        # Verify error details
        self.assertEqual(context.exception.task_id, task.id)
        self.assertEqual(context.exception.status, TaskStatus.COMPLETED.value)

    def test_execute_raises_error_when_starting_failed_task(self):
        """Test execute raises TaskAlreadyFinishedError when starting FAILED task"""
        # Create a failed task
        task = Task(name="Test Task", priority=1, status=TaskStatus.FAILED)
        task.id = self.repository.generate_next_id()
        task.actual_start = "2024-01-01 10:00:00"
        task.actual_end = "2024-01-01 11:00:00"
        self.repository.save(task)

        # Try to start the failed task - should raise error
        input_dto = StartTaskInput(task_id=task.id)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.use_case.execute(input_dto)

        # Verify error details
        self.assertEqual(context.exception.task_id, task.id)
        self.assertEqual(context.exception.status, TaskStatus.FAILED.value)

    def test_execute_does_not_modify_completed_task_state(self):
        """Test execute does not modify state when attempted on COMPLETED task"""
        # Create and complete a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        task.actual_start = "2024-01-01 10:00:00"
        task.actual_end = "2024-01-01 12:00:00"
        self.repository.save(task)

        # Try to start the completed task
        input_dto = StartTaskInput(task_id=task.id)

        with contextlib.suppress(TaskAlreadyFinishedError):
            self.use_case.execute(input_dto)

        # Verify task state remains unchanged
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.COMPLETED)
        self.assertEqual(retrieved.actual_start, "2024-01-01 10:00:00")
        self.assertEqual(retrieved.actual_end, "2024-01-01 12:00:00")


if __name__ == "__main__":
    unittest.main()
