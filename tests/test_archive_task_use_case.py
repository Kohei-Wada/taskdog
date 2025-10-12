"""Tests for ArchiveTaskUseCase."""

import tempfile
import unittest

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.archive_task import ArchiveTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class ArchiveTaskUseCaseTest(unittest.TestCase):
    """Test cases for ArchiveTaskUseCase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.temp_file.write("[]")
        self.temp_file.close()

        self.repository = JsonTaskRepository(self.temp_file.name)
        self.use_case = ArchiveTaskUseCase(self.repository)

    def test_archive_orphan_mode(self):
        """Test archiving a task in orphan mode."""
        # Create parent and child tasks
        parent = self.repository.create(name="Parent Task", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=parent.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=parent.id)

        # Archive parent in orphan mode
        input_dto = ArchiveTaskInput(task_id=parent.id, cascade=False)
        archived_count = self.use_case.execute(input_dto)

        # Verify
        self.assertEqual(archived_count, 1)

        # Parent should be archived
        parent_after = self.repository.get_by_id(parent.id)
        self.assertIsNotNone(parent_after)
        self.assertEqual(parent_after.status, TaskStatus.ARCHIVED)

        # Children should still exist but with parent_id = None
        child1_after = self.repository.get_by_id(child1.id)
        child2_after = self.repository.get_by_id(child2.id)
        self.assertIsNotNone(child1_after)
        self.assertIsNotNone(child2_after)
        self.assertIsNone(child1_after.parent_id)
        self.assertIsNone(child2_after.parent_id)
        self.assertEqual(child1_after.status, TaskStatus.PENDING)
        self.assertEqual(child2_after.status, TaskStatus.PENDING)

    def test_archive_cascade_mode(self):
        """Test archiving a task in cascade mode."""
        # Create hierarchy: parent -> child -> grandchild
        parent = self.repository.create(name="Parent", priority=1)
        child = self.repository.create(name="Child", priority=1, parent_id=parent.id)
        grandchild = self.repository.create(name="Grandchild", priority=1, parent_id=child.id)

        # Archive parent in cascade mode
        input_dto = ArchiveTaskInput(task_id=parent.id, cascade=True)
        archived_count = self.use_case.execute(input_dto)

        # Verify all tasks archived
        self.assertEqual(archived_count, 3)

        parent_after = self.repository.get_by_id(parent.id)
        child_after = self.repository.get_by_id(child.id)
        grandchild_after = self.repository.get_by_id(grandchild.id)

        self.assertEqual(parent_after.status, TaskStatus.ARCHIVED)
        self.assertEqual(child_after.status, TaskStatus.ARCHIVED)
        self.assertEqual(grandchild_after.status, TaskStatus.ARCHIVED)

        # Hierarchy should be preserved
        self.assertEqual(child_after.parent_id, parent.id)
        self.assertEqual(grandchild_after.parent_id, child.id)

    def test_archive_cascade_with_multiple_branches(self):
        """Test cascade archiving with multiple child branches."""
        # Create tree structure
        root = self.repository.create(name="Root", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=root.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=root.id)
        grandchild1 = self.repository.create(name="Grandchild 1", priority=1, parent_id=child1.id)
        grandchild2 = self.repository.create(name="Grandchild 2", priority=1, parent_id=child2.id)

        # Archive root in cascade mode
        input_dto = ArchiveTaskInput(task_id=root.id, cascade=True)
        archived_count = self.use_case.execute(input_dto)

        # Verify all 5 tasks archived
        self.assertEqual(archived_count, 5)

        for task_id in [root.id, child1.id, child2.id, grandchild1.id, grandchild2.id]:
            task = self.repository.get_by_id(task_id)
            self.assertIsNotNone(task)
            self.assertEqual(task.status, TaskStatus.ARCHIVED)

    def test_archive_leaf_task(self):
        """Test archiving a task with no children."""
        # Create task without children
        task = self.repository.create(name="Leaf Task", priority=1)

        # Archive in orphan mode
        input_dto = ArchiveTaskInput(task_id=task.id, cascade=False)
        archived_count = self.use_case.execute(input_dto)

        # Verify
        self.assertEqual(archived_count, 1)
        task_after = self.repository.get_by_id(task.id)
        self.assertEqual(task_after.status, TaskStatus.ARCHIVED)

    def test_archive_leaf_task_cascade(self):
        """Test archiving a leaf task in cascade mode."""
        # Create task without children
        task = self.repository.create(name="Leaf Task", priority=1)

        # Archive in cascade mode
        input_dto = ArchiveTaskInput(task_id=task.id, cascade=True)
        archived_count = self.use_case.execute(input_dto)

        # Verify (should work same as orphan for leaf task)
        self.assertEqual(archived_count, 1)
        task_after = self.repository.get_by_id(task.id)
        self.assertEqual(task_after.status, TaskStatus.ARCHIVED)

    def test_archive_nonexistent_task(self):
        """Test archiving a task that doesn't exist."""
        input_dto = ArchiveTaskInput(task_id=999, cascade=False)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_archive_orphan_preserves_siblings(self):
        """Test that orphan mode doesn't affect sibling tasks."""
        # Create parent with multiple children
        parent = self.repository.create(name="Parent", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=parent.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=parent.id)
        other_task = self.repository.create(name="Other Task", priority=1)

        # Archive parent in orphan mode
        input_dto = ArchiveTaskInput(task_id=parent.id, cascade=False)
        self.use_case.execute(input_dto)

        # Verify parent archived
        parent_after = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_after.status, TaskStatus.ARCHIVED)

        # Verify children orphaned but not archived
        child1_after = self.repository.get_by_id(child1.id)
        child2_after = self.repository.get_by_id(child2.id)
        other_after = self.repository.get_by_id(other_task.id)

        self.assertIsNotNone(child1_after)
        self.assertIsNotNone(child2_after)
        self.assertIsNotNone(other_after)
        self.assertIsNone(child1_after.parent_id)
        self.assertIsNone(child2_after.parent_id)
        self.assertEqual(child1_after.status, TaskStatus.PENDING)
        self.assertEqual(child2_after.status, TaskStatus.PENDING)
        self.assertEqual(other_after.status, TaskStatus.PENDING)

    def test_archive_completed_task(self):
        """Test archiving an already completed task."""
        # Create completed task
        task = self.repository.create(name="Completed Task", priority=1)
        task.status = TaskStatus.COMPLETED
        self.repository.save(task)

        # Archive it
        input_dto = ArchiveTaskInput(task_id=task.id, cascade=False)
        archived_count = self.use_case.execute(input_dto)

        # Verify archived
        self.assertEqual(archived_count, 1)
        task_after = self.repository.get_by_id(task.id)
        self.assertEqual(task_after.status, TaskStatus.ARCHIVED)

    def test_archive_in_progress_task(self):
        """Test archiving an in-progress task."""
        # Create in-progress task
        task = self.repository.create(name="In Progress Task", priority=1)
        task.status = TaskStatus.IN_PROGRESS
        self.repository.save(task)

        # Archive it
        input_dto = ArchiveTaskInput(task_id=task.id, cascade=False)
        archived_count = self.use_case.execute(input_dto)

        # Verify archived
        self.assertEqual(archived_count, 1)
        task_after = self.repository.get_by_id(task.id)
        self.assertEqual(task_after.status, TaskStatus.ARCHIVED)


if __name__ == "__main__":
    unittest.main()
