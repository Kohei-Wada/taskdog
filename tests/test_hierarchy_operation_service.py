"""Tests for HierarchyOperationService."""

import tempfile
import unittest

from application.services.hierarchy_operation_service import HierarchyOperationService
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class HierarchyOperationServiceTest(unittest.TestCase):
    """Test cases for HierarchyOperationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.temp_file.write("[]")
        self.temp_file.close()

        self.repository = JsonTaskRepository(self.temp_file.name)
        self.service = HierarchyOperationService()

    def test_execute_cascade_single_task(self):
        """Test cascade execution on a single task with no children."""
        # Create a leaf task
        task = self.repository.create(name="Leaf Task", priority=1)

        # Track operations
        processed_ids = []

        def track_operation(task_id: int):
            processed_ids.append(task_id)

        # Execute cascade
        count = self.service.execute_cascade(task.id, self.repository, track_operation)

        # Verify
        self.assertEqual(count, 1)
        self.assertEqual(processed_ids, [task.id])

    def test_execute_cascade_with_children(self):
        """Test cascade execution processes children before parent."""
        # Create hierarchy: parent -> child1, child2
        parent = self.repository.create(name="Parent", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=parent.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=parent.id)

        # Track operation order
        processed_ids = []

        def track_operation(task_id: int):
            processed_ids.append(task_id)

        # Execute cascade
        count = self.service.execute_cascade(parent.id, self.repository, track_operation)

        # Verify count
        self.assertEqual(count, 3)

        # Verify children processed before parent
        self.assertIn(child1.id, processed_ids)
        self.assertIn(child2.id, processed_ids)
        self.assertIn(parent.id, processed_ids)
        self.assertEqual(processed_ids[-1], parent.id)  # Parent processed last

    def test_execute_cascade_with_deep_hierarchy(self):
        """Test cascade execution on deep hierarchy."""
        # Create hierarchy: root -> child -> grandchild
        root = self.repository.create(name="Root", priority=1)
        child = self.repository.create(name="Child", priority=1, parent_id=root.id)
        grandchild = self.repository.create(name="Grandchild", priority=1, parent_id=child.id)

        # Track operation order
        processed_ids = []

        def track_operation(task_id: int):
            processed_ids.append(task_id)

        # Execute cascade
        count = self.service.execute_cascade(root.id, self.repository, track_operation)

        # Verify
        self.assertEqual(count, 3)
        # Grandchild should be processed first, then child, then root
        self.assertEqual(processed_ids[0], grandchild.id)
        self.assertEqual(processed_ids[1], child.id)
        self.assertEqual(processed_ids[2], root.id)

    def test_execute_cascade_with_multiple_branches(self):
        """Test cascade execution with multiple child branches."""
        # Create tree structure
        root = self.repository.create(name="Root", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=root.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=root.id)
        grandchild1 = self.repository.create(name="Grandchild 1", priority=1, parent_id=child1.id)
        grandchild2 = self.repository.create(name="Grandchild 2", priority=1, parent_id=child2.id)

        # Track operations
        processed_ids = []

        def track_operation(task_id: int):
            processed_ids.append(task_id)

        # Execute cascade
        count = self.service.execute_cascade(root.id, self.repository, track_operation)

        # Verify all tasks processed
        self.assertEqual(count, 5)
        self.assertEqual(len(processed_ids), 5)

        # Verify root is processed last
        self.assertEqual(processed_ids[-1], root.id)

        # Verify grandchildren processed before their parents
        grandchild1_idx = processed_ids.index(grandchild1.id)
        child1_idx = processed_ids.index(child1.id)
        self.assertLess(grandchild1_idx, child1_idx)

        grandchild2_idx = processed_ids.index(grandchild2.id)
        child2_idx = processed_ids.index(child2.id)
        self.assertLess(grandchild2_idx, child2_idx)

    def test_execute_orphan_single_task(self):
        """Test orphan execution on a task with no children."""
        # Create a leaf task
        task = self.repository.create(name="Leaf Task", priority=1)

        # Track operations
        processed_ids = []

        def track_operation(task_id: int):
            processed_ids.append(task_id)

        # Execute orphan
        count = self.service.execute_orphan(task.id, self.repository, track_operation)

        # Verify
        self.assertEqual(count, 1)
        self.assertEqual(processed_ids, [task.id])

    def test_execute_orphan_with_children(self):
        """Test orphan execution sets children's parent_id to None."""
        # Create parent and children
        parent = self.repository.create(name="Parent", priority=1)
        child1 = self.repository.create(name="Child 1", priority=1, parent_id=parent.id)
        child2 = self.repository.create(name="Child 2", priority=1, parent_id=parent.id)

        # Track operations
        processed_ids = []

        def track_operation(task_id: int):
            processed_ids.append(task_id)

        # Execute orphan
        count = self.service.execute_orphan(parent.id, self.repository, track_operation)

        # Verify only parent processed
        self.assertEqual(count, 1)
        self.assertEqual(processed_ids, [parent.id])

        # Verify children are orphaned (parent_id set to None)
        child1_after = self.repository.get_by_id(child1.id)
        child2_after = self.repository.get_by_id(child2.id)
        self.assertIsNotNone(child1_after)
        self.assertIsNotNone(child2_after)
        self.assertIsNone(child1_after.parent_id)
        self.assertIsNone(child2_after.parent_id)

    def test_execute_orphan_preserves_grandchildren(self):
        """Test orphan execution preserves grandchildren relationships."""
        # Create hierarchy: parent -> child -> grandchild
        parent = self.repository.create(name="Parent", priority=1)
        child = self.repository.create(name="Child", priority=1, parent_id=parent.id)
        grandchild = self.repository.create(name="Grandchild", priority=1, parent_id=child.id)

        # Track operations
        processed_ids = []

        def track_operation(task_id: int):
            processed_ids.append(task_id)

        # Execute orphan on parent
        count = self.service.execute_orphan(parent.id, self.repository, track_operation)

        # Verify only parent processed
        self.assertEqual(count, 1)
        self.assertEqual(processed_ids, [parent.id])

        # Verify child is orphaned but grandchild relationship preserved
        child_after = self.repository.get_by_id(child.id)
        grandchild_after = self.repository.get_by_id(grandchild.id)
        self.assertIsNotNone(child_after)
        self.assertIsNotNone(grandchild_after)
        self.assertIsNone(child_after.parent_id)  # Child orphaned
        self.assertEqual(grandchild_after.parent_id, child.id)  # Grandchild still has parent

    def test_operation_callback_receives_correct_task_id(self):
        """Test that operation callback receives correct task IDs."""
        # Create tasks
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        # Track what task IDs are passed to operation
        received_ids = []

        def capture_task_id(task_id: int):
            received_ids.append(task_id)

        # Execute operations
        self.service.execute_orphan(task1.id, self.repository, capture_task_id)
        self.service.execute_cascade(task2.id, self.repository, capture_task_id)

        # Verify correct IDs received
        self.assertEqual(received_ids, [task1.id, task2.id])


if __name__ == "__main__":
    unittest.main()
