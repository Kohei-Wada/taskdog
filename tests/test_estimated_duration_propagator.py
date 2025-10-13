"""Tests for EstimatedDurationPropagator."""

import os
import tempfile
import unittest

from application.services.estimated_duration_propagator import EstimatedDurationPropagator
from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestEstimatedDurationPropagator(unittest.TestCase):
    """Test cases for EstimatedDurationPropagator."""

    def setUp(self):
        """Create temporary file and initialize propagator for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.propagator = EstimatedDurationPropagator(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_propagate_updates_parent_with_child_sum(self):
        """Test that parent's estimated_duration becomes sum of children."""
        # Create parent
        parent = Task(name="Parent", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create children with estimated_duration
        child1 = Task(name="Child 1", priority=1, parent_id=parent.id, estimated_duration=5.0)
        child1.id = self.repository.generate_next_id()
        self.repository.save(child1)

        child2 = Task(name="Child 2", priority=1, parent_id=parent.id, estimated_duration=3.0)
        child2.id = self.repository.generate_next_id()
        self.repository.save(child2)

        # Propagate
        result = self.propagator.propagate(parent.id)

        # Verify parent's estimated_duration is sum of children
        self.assertIsNotNone(result)
        self.assertEqual(result.estimated_duration, 8.0)

        # Verify it's persisted
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.estimated_duration, 8.0)

    def test_propagate_recursively_updates_grandparent(self):
        """Test that propagation updates grandparent recursively."""
        # Create grandparent
        grandparent = Task(name="Grandparent", priority=1)
        grandparent.id = self.repository.generate_next_id()
        self.repository.save(grandparent)

        # Create parent as child of grandparent
        parent = Task(name="Parent", priority=1, parent_id=grandparent.id)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child with estimated_duration
        child = Task(name="Child", priority=1, parent_id=parent.id, estimated_duration=10.0)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Propagate from parent
        self.propagator.propagate(parent.id)

        # Verify parent's estimated_duration
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.estimated_duration, 10.0)

        # Verify grandparent's estimated_duration is also updated
        grandparent_updated = self.repository.get_by_id(grandparent.id)
        self.assertEqual(grandparent_updated.estimated_duration, 10.0)

    def test_propagate_returns_none_for_nonexistent_parent(self):
        """Test that propagate returns None if parent doesn't exist."""
        result = self.propagator.propagate(999)
        self.assertIsNone(result)

    def test_propagate_returns_none_for_parent_without_children(self):
        """Test that propagate returns None if parent has no children."""
        parent = Task(name="Parent", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        result = self.propagator.propagate(parent.id)
        self.assertIsNone(result)

    def test_propagate_skips_archived_parent(self):
        """Test that propagate returns None for archived parent tasks."""
        # Create archived parent
        parent = Task(name="Parent", priority=1, status=TaskStatus.ARCHIVED)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child with estimated_duration
        child = Task(name="Child", priority=1, parent_id=parent.id, estimated_duration=5.0)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Propagate
        result = self.propagator.propagate(parent.id)

        # Verify parent was not updated
        self.assertIsNone(result)
        parent_unchanged = self.repository.get_by_id(parent.id)
        self.assertIsNone(parent_unchanged.estimated_duration)

    def test_propagate_handles_children_without_estimates(self):
        """Test that propagate returns None when no children have estimated_duration."""
        # Create parent
        parent = Task(name="Parent", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create children without estimated_duration
        child1 = Task(name="Child 1", priority=1, parent_id=parent.id)
        child1.id = self.repository.generate_next_id()
        self.repository.save(child1)

        child2 = Task(name="Child 2", priority=1, parent_id=parent.id)
        child2.id = self.repository.generate_next_id()
        self.repository.save(child2)

        # Propagate
        result = self.propagator.propagate(parent.id)

        # Verify parent was not updated
        self.assertIsNone(result)
        parent_unchanged = self.repository.get_by_id(parent.id)
        self.assertIsNone(parent_unchanged.estimated_duration)

    def test_propagate_handles_mixed_children_estimates(self):
        """Test that propagate sums only children with estimated_duration."""
        # Create parent
        parent = Task(name="Parent", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create children with mixed estimated_duration
        child1 = Task(name="Child 1", priority=1, parent_id=parent.id, estimated_duration=5.0)
        child1.id = self.repository.generate_next_id()
        self.repository.save(child1)

        child2 = Task(name="Child 2", priority=1, parent_id=parent.id)  # No estimate
        child2.id = self.repository.generate_next_id()
        self.repository.save(child2)

        child3 = Task(name="Child 3", priority=1, parent_id=parent.id, estimated_duration=3.0)
        child3.id = self.repository.generate_next_id()
        self.repository.save(child3)

        # Propagate
        result = self.propagator.propagate(parent.id)

        # Verify parent's estimated_duration is sum of only children with estimates
        self.assertIsNotNone(result)
        self.assertEqual(result.estimated_duration, 8.0)


if __name__ == "__main__":
    unittest.main()
