import unittest

from domain.entities.task import Task, TaskStatus
from domain.services.task_eligibility_checker import TaskEligibilityChecker


class TestTaskEligibilityChecker(unittest.TestCase):
    """Test cases for TaskEligibilityChecker"""

    def test_can_be_started_with_no_children_returns_true(self):
        """Test can_be_started returns True when task has no children"""
        task = Task(name="Test Task", priority=1)
        children = []

        result = TaskEligibilityChecker.can_be_started(task, children)

        self.assertTrue(result)

    def test_can_be_started_with_completed_task_returns_false(self):
        """Test can_be_started returns False when task is COMPLETED"""
        task = Task(name="Completed Task", priority=1, status=TaskStatus.COMPLETED)
        children = []

        result = TaskEligibilityChecker.can_be_started(task, children)

        self.assertFalse(result)

    def test_can_be_started_with_failed_task_returns_false(self):
        """Test can_be_started returns False when task is FAILED"""
        task = Task(name="Failed Task", priority=1, status=TaskStatus.FAILED)
        children = []

        result = TaskEligibilityChecker.can_be_started(task, children)

        self.assertFalse(result)

    def test_can_be_started_with_pending_task_returns_true(self):
        """Test can_be_started returns True when task is PENDING"""
        task = Task(name="Pending Task", priority=1, status=TaskStatus.PENDING)
        children = []

        result = TaskEligibilityChecker.can_be_started(task, children)

        self.assertTrue(result)

    def test_can_be_started_with_in_progress_task_returns_true(self):
        """Test can_be_started returns True when task is IN_PROGRESS"""
        task = Task(name="In Progress Task", priority=1, status=TaskStatus.IN_PROGRESS)
        children = []

        result = TaskEligibilityChecker.can_be_started(task, children)

        self.assertTrue(result)

    def test_can_be_completed_with_all_completed_children_returns_true(self):
        """Test can_be_completed returns True when all children are completed"""
        task = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        child1 = Task(name="Child 1", priority=2, status=TaskStatus.COMPLETED)
        child2 = Task(name="Child 2", priority=3, status=TaskStatus.COMPLETED)
        children = [child1, child2]

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertTrue(result)

    def test_can_be_completed_with_no_children_returns_true(self):
        """Test can_be_completed returns True when task has no children"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        children = []

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertTrue(result)

    def test_can_be_completed_with_pending_child_returns_false(self):
        """Test can_be_completed returns False when child is PENDING"""
        task = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        child1 = Task(name="Child 1", priority=2, status=TaskStatus.COMPLETED)
        child2 = Task(name="Child 2", priority=3, status=TaskStatus.PENDING)
        children = [child1, child2]

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertFalse(result)

    def test_can_be_completed_with_in_progress_child_returns_false(self):
        """Test can_be_completed returns False when child is IN_PROGRESS"""
        task = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        child1 = Task(name="Child 1", priority=2, status=TaskStatus.COMPLETED)
        child2 = Task(name="Child 2", priority=3, status=TaskStatus.IN_PROGRESS)
        children = [child1, child2]

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertFalse(result)

    def test_can_be_completed_with_failed_child_returns_false(self):
        """Test can_be_completed returns False when child is FAILED"""
        task = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        child1 = Task(name="Child 1", priority=2, status=TaskStatus.COMPLETED)
        child2 = Task(name="Child 2", priority=3, status=TaskStatus.FAILED)
        children = [child1, child2]

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertFalse(result)

    def test_can_be_completed_with_all_incomplete_children_returns_false(self):
        """Test can_be_completed returns False when all children are incomplete"""
        task = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        child1 = Task(name="Child 1", priority=2, status=TaskStatus.PENDING)
        child2 = Task(name="Child 2", priority=3, status=TaskStatus.IN_PROGRESS)
        child3 = Task(name="Child 3", priority=4, status=TaskStatus.FAILED)
        children = [child1, child2, child3]

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertFalse(result)

    def test_can_be_completed_with_pending_task_returns_false(self):
        """Test can_be_completed returns False when task is PENDING"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        children = []

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertFalse(result)

    def test_can_be_completed_with_completed_task_returns_false(self):
        """Test can_be_completed returns False when task is already COMPLETED"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        children = []

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertFalse(result)

    def test_can_be_completed_with_failed_task_returns_false(self):
        """Test can_be_completed returns False when task is FAILED"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.FAILED)
        children = []

        result = TaskEligibilityChecker.can_be_completed(task, children)

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
