"""Tests for RemoveTaskUseCase."""

import unittest
from application.use_cases.remove_task import RemoveTaskUseCase
from application.dto.remove_task_input import RemoveTaskInput
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskNotFoundException
import tempfile
import json


class RemoveTaskUseCaseTest(unittest.TestCase):
    """Test cases for RemoveTaskUseCase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
        self.temp_file.write("[]")
        self.temp_file.close()

        self.repository = JsonTaskRepository(self.temp_file.name)
        self.use_case = RemoveTaskUseCase(self.repository)

    def test_remove_orphan_mode(self):
        """Test removing a task in orphan mode."""
        # Create parent and child tasks
        parent = self.repository.create(name="Parent Task", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=parent.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=parent.id)

        # Remove parent in orphan mode
        input_dto = RemoveTaskInput(task_id=parent.id, cascade=False)
        removed_count = self.use_case.execute(input_dto)

        # Verify
        self.assertEqual(removed_count, 1)
        self.assertIsNone(self.repository.get_by_id(parent.id))

        # Children should still exist but with parent_id = None
        child1_after = self.repository.get_by_id(child1.id)
        child2_after = self.repository.get_by_id(child2.id)
        self.assertIsNotNone(child1_after)
        self.assertIsNotNone(child2_after)
        self.assertIsNone(child1_after.parent_id)
        self.assertIsNone(child2_after.parent_id)

    def test_remove_cascade_mode(self):
        """Test removing a task in cascade mode."""
        # Create hierarchy: parent -> child -> grandchild
        parent = self.repository.create(name="Parent", priority=1)
        child = self.repository.create(name="Child", priority=1, parent_id=parent.id)
        grandchild = self.repository.create(
            name="Grandchild", priority=1, parent_id=child.id
        )

        # Remove parent in cascade mode
        input_dto = RemoveTaskInput(task_id=parent.id, cascade=True)
        removed_count = self.use_case.execute(input_dto)

        # Verify all tasks removed
        self.assertEqual(removed_count, 3)
        self.assertIsNone(self.repository.get_by_id(parent.id))
        self.assertIsNone(self.repository.get_by_id(child.id))
        self.assertIsNone(self.repository.get_by_id(grandchild.id))

    def test_remove_cascade_with_multiple_branches(self):
        """Test cascade removal with multiple child branches."""
        # Create tree structure
        root = self.repository.create(name="Root", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=root.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=root.id)
        grandchild1 = self.repository.create(
            name="Grandchild 1", priority=1, parent_id=child1.id
        )
        grandchild2 = self.repository.create(
            name="Grandchild 2", priority=1, parent_id=child2.id
        )

        # Remove root in cascade mode
        input_dto = RemoveTaskInput(task_id=root.id, cascade=True)
        removed_count = self.use_case.execute(input_dto)

        # Verify all 5 tasks removed
        self.assertEqual(removed_count, 5)
        self.assertIsNone(self.repository.get_by_id(root.id))
        self.assertIsNone(self.repository.get_by_id(child1.id))
        self.assertIsNone(self.repository.get_by_id(child2.id))
        self.assertIsNone(self.repository.get_by_id(grandchild1.id))
        self.assertIsNone(self.repository.get_by_id(grandchild2.id))

    def test_remove_leaf_task(self):
        """Test removing a task with no children."""
        # Create task without children
        task = self.repository.create(name="Leaf Task", priority=1)

        # Remove in orphan mode
        input_dto = RemoveTaskInput(task_id=task.id, cascade=False)
        removed_count = self.use_case.execute(input_dto)

        # Verify
        self.assertEqual(removed_count, 1)
        self.assertIsNone(self.repository.get_by_id(task.id))

    def test_remove_leaf_task_cascade(self):
        """Test removing a leaf task in cascade mode."""
        # Create task without children
        task = self.repository.create(name="Leaf Task", priority=1)

        # Remove in cascade mode
        input_dto = RemoveTaskInput(task_id=task.id, cascade=True)
        removed_count = self.use_case.execute(input_dto)

        # Verify (should work same as orphan for leaf task)
        self.assertEqual(removed_count, 1)
        self.assertIsNone(self.repository.get_by_id(task.id))

    def test_remove_nonexistent_task(self):
        """Test removing a task that doesn't exist."""
        input_dto = RemoveTaskInput(task_id=999, cascade=False)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_orphan_preserves_siblings(self):
        """Test that orphan mode doesn't affect sibling tasks."""
        # Create parent with multiple children
        parent = self.repository.create(name="Parent", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=parent.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=parent.id)
        other_task = self.repository.create(name="Other Task", priority=1)

        # Remove parent in orphan mode
        input_dto = RemoveTaskInput(task_id=parent.id, cascade=False)
        self.use_case.execute(input_dto)

        # Verify siblings and unrelated tasks unaffected
        child1_after = self.repository.get_by_id(child1.id)
        child2_after = self.repository.get_by_id(child2.id)
        other_after = self.repository.get_by_id(other_task.id)

        self.assertIsNotNone(child1_after)
        self.assertIsNotNone(child2_after)
        self.assertIsNotNone(other_after)
        self.assertIsNone(child1_after.parent_id)
        self.assertIsNone(child2_after.parent_id)
        self.assertIsNone(other_after.parent_id)  # Was already None


if __name__ == "__main__":
    unittest.main()
