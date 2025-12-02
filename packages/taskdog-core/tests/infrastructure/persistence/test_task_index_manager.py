"""Tests for TaskIndexManager."""

import pytest

from taskdog_core.domain.entities.task import Task
from taskdog_core.infrastructure.persistence.task_index_manager import TaskIndexManager


class TestTaskIndexManager:
    """Test suite for TaskIndexManager."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.task1 = Task(id=1, name="Task 1", priority=1)
        self.task2 = Task(id=2, name="Task 2", priority=2)
        self.task3 = Task(id=3, name="Task 3", priority=3)
        self.tasks = [self.task1, self.task2, self.task3]

    def test_init_without_tasks(self):
        """Test initialization without tasks."""
        manager = TaskIndexManager()

        assert manager.get_by_id(1) is None
        assert manager.has_task(1) is False

    def test_init_with_tasks(self):
        """Test initialization with tasks builds indexes."""
        manager = TaskIndexManager(self.tasks)

        assert manager.get_by_id(1) == self.task1
        assert manager.get_by_id(2) == self.task2
        assert manager.get_by_id(3) == self.task3

    def test_build_indexes_creates_task_index(self):
        """Test build_indexes creates task index correctly."""
        manager = TaskIndexManager()
        manager.build_indexes(self.tasks)

        assert manager.get_by_id(1) == self.task1
        assert manager.get_by_id(2) == self.task2
        assert manager.get_by_id(3) == self.task3

    def test_build_indexes_creates_position_index(self):
        """Test build_indexes creates position index correctly."""
        manager = TaskIndexManager()
        manager.build_indexes(self.tasks)

        assert manager.get_position(1) == 0
        assert manager.get_position(2) == 1
        assert manager.get_position(3) == 2

    def test_build_indexes_skips_tasks_without_id(self):
        """Test build_indexes skips tasks without ID."""
        task_without_id = Task(id=None, name="No ID", priority=1)
        tasks_with_none = [self.task1, task_without_id, self.task2]
        manager = TaskIndexManager()

        manager.build_indexes(tasks_with_none)

        assert manager.get_by_id(1) == self.task1
        assert manager.get_by_id(2) == self.task2
        # Task without ID should not be indexed
        assert manager.get_by_id(None) is None

    def test_get_by_id_returns_task_when_exists(self):
        """Test get_by_id returns task when it exists."""
        manager = TaskIndexManager(self.tasks)

        result = manager.get_by_id(2)

        assert result == self.task2

    def test_get_by_id_returns_none_when_not_exists(self):
        """Test get_by_id returns None when task doesn't exist."""
        manager = TaskIndexManager(self.tasks)

        result = manager.get_by_id(999)

        assert result is None

    def test_get_by_ids_returns_existing_tasks(self):
        """Test get_by_ids returns dictionary of existing tasks."""
        manager = TaskIndexManager(self.tasks)

        result = manager.get_by_ids([1, 2, 3])

        assert len(result) == 3
        assert result[1] == self.task1
        assert result[2] == self.task2
        assert result[3] == self.task3

    def test_get_by_ids_skips_non_existing_tasks(self):
        """Test get_by_ids skips non-existing task IDs."""
        manager = TaskIndexManager(self.tasks)

        result = manager.get_by_ids([1, 999, 2, 888])

        assert len(result) == 2
        assert result[1] == self.task1
        assert result[2] == self.task2
        assert 999 not in result
        assert 888 not in result

    def test_get_by_ids_returns_empty_dict_when_no_matches(self):
        """Test get_by_ids returns empty dictionary when no IDs match."""
        manager = TaskIndexManager(self.tasks)

        result = manager.get_by_ids([999, 888, 777])

        assert result == {}

    def test_get_by_ids_with_empty_list(self):
        """Test get_by_ids with empty list returns empty dictionary."""
        manager = TaskIndexManager(self.tasks)

        result = manager.get_by_ids([])

        assert result == {}

    def test_get_position_returns_position_when_exists(self):
        """Test get_position returns correct position."""
        manager = TaskIndexManager(self.tasks)

        assert manager.get_position(1) == 0
        assert manager.get_position(2) == 1
        assert manager.get_position(3) == 2

    def test_get_position_returns_none_when_not_exists(self):
        """Test get_position returns None when task doesn't exist."""
        manager = TaskIndexManager(self.tasks)

        result = manager.get_position(999)

        assert result is None

    def test_add_task_adds_to_both_indexes(self):
        """Test add_task adds task to both indexes."""
        manager = TaskIndexManager()
        new_task = Task(id=10, name="New Task", priority=1)

        manager.add_task(new_task, position=0)

        assert manager.get_by_id(10) == new_task
        assert manager.get_position(10) == 0

    def test_add_task_raises_value_error_when_task_has_no_id(self):
        """Test add_task raises ValueError when task has no ID."""
        manager = TaskIndexManager()
        task_without_id = Task(id=None, name="No ID", priority=1)

        with pytest.raises(ValueError) as exc_info:
            manager.add_task(task_without_id, position=0)

        assert "Cannot index task without ID" in str(exc_info.value)

    def test_update_task_updates_task_in_index(self):
        """Test update_task updates task in task_index."""
        manager = TaskIndexManager(self.tasks)
        updated_task = Task(id=2, name="Updated Task 2", priority=5)

        manager.update_task(updated_task)

        result = manager.get_by_id(2)
        assert result.name == "Updated Task 2"
        assert result.priority == 5

    def test_update_task_does_not_update_position(self):
        """Test update_task doesn't change position index."""
        manager = TaskIndexManager(self.tasks)
        updated_task = Task(id=2, name="Updated", priority=5)

        manager.update_task(updated_task)

        # Position should remain the same
        assert manager.get_position(2) == 1

    def test_update_task_raises_value_error_when_task_has_no_id(self):
        """Test update_task raises ValueError when task has no ID."""
        manager = TaskIndexManager(self.tasks)
        task_without_id = Task(id=None, name="No ID", priority=1)

        with pytest.raises(ValueError) as exc_info:
            manager.update_task(task_without_id)

        assert "Cannot update task without ID" in str(exc_info.value)

    def test_update_task_raises_value_error_when_task_not_in_index(self):
        """Test update_task raises ValueError when task doesn't exist."""
        manager = TaskIndexManager(self.tasks)
        new_task = Task(id=999, name="Non-existent", priority=1)

        with pytest.raises(ValueError) as exc_info:
            manager.update_task(new_task)

        assert "Task with ID 999 not found in index" in str(exc_info.value)

    def test_remove_task_removes_from_both_indexes(self):
        """Test remove_task removes from both indexes."""
        manager = TaskIndexManager(self.tasks)

        manager.remove_task(2)

        assert manager.get_by_id(2) is None
        assert manager.get_position(2) is None
        assert manager.has_task(2) is False

    def test_remove_task_with_non_existent_id(self):
        """Test remove_task doesn't raise error for non-existent ID."""
        manager = TaskIndexManager(self.tasks)

        # Should not raise error
        manager.remove_task(999)

        # Other tasks should still be present
        assert manager.has_task(1) is True
        assert manager.has_task(2) is True

    def test_has_task_returns_true_when_task_exists(self):
        """Test has_task returns True when task exists."""
        manager = TaskIndexManager(self.tasks)

        assert manager.has_task(1) is True
        assert manager.has_task(2) is True
        assert manager.has_task(3) is True

    def test_has_task_returns_false_when_task_does_not_exist(self):
        """Test has_task returns False when task doesn't exist."""
        manager = TaskIndexManager(self.tasks)

        assert manager.has_task(999) is False

    def test_rebuild_position_index_updates_positions(self):
        """Test rebuild_position_index updates position index."""
        manager = TaskIndexManager(self.tasks)
        # Reorder tasks
        reordered_tasks = [self.task3, self.task1, self.task2]

        manager.rebuild_position_index(reordered_tasks)

        assert manager.get_position(3) == 0
        assert manager.get_position(1) == 1
        assert manager.get_position(2) == 2

    def test_rebuild_position_index_does_not_affect_task_index(self):
        """Test rebuild_position_index doesn't change task_index."""
        manager = TaskIndexManager(self.tasks)
        reordered_tasks = [self.task3, self.task1, self.task2]

        manager.rebuild_position_index(reordered_tasks)

        # Task index should still have all tasks
        assert manager.get_by_id(1) == self.task1
        assert manager.get_by_id(2) == self.task2
        assert manager.get_by_id(3) == self.task3

    def test_rebuild_position_index_with_fewer_tasks(self):
        """Test rebuild_position_index when task list is smaller."""
        manager = TaskIndexManager(self.tasks)
        # Remove task2 from list
        smaller_list = [self.task1, self.task3]

        manager.rebuild_position_index(smaller_list)

        assert manager.get_position(1) == 0
        assert manager.get_position(3) == 1
        # Task 2's position is removed but task_index still has it
        assert manager.get_position(2) is None
        assert manager.get_by_id(2) == self.task2

    def test_rebuild_position_index_skips_tasks_without_id(self):
        """Test rebuild_position_index skips tasks without ID."""
        manager = TaskIndexManager(self.tasks)
        task_without_id = Task(id=None, name="No ID", priority=1)
        tasks_with_none = [self.task1, task_without_id, self.task2]

        manager.rebuild_position_index(tasks_with_none)

        # Should only index tasks with IDs
        assert manager.get_position(1) == 0
        assert manager.get_position(2) == 2

    def test_index_consistency_after_multiple_operations(self):
        """Test indexes remain consistent after multiple operations."""
        manager = TaskIndexManager()

        # Add tasks
        manager.add_task(self.task1, 0)
        manager.add_task(self.task2, 1)
        assert manager.get_by_id(1) == self.task1
        assert manager.get_position(1) == 0

        # Update task
        updated_task1 = Task(id=1, name="Updated Task 1", priority=10)
        manager.update_task(updated_task1)
        assert manager.get_by_id(1).name == "Updated Task 1"
        assert manager.get_position(1) == 0

        # Remove task
        manager.remove_task(2)
        assert manager.get_by_id(2) is None

        # Add new task
        task3 = Task(id=3, name="Task 3", priority=3)
        manager.add_task(task3, 1)
        assert manager.get_by_id(3) == task3

        # Rebuild positions
        manager.rebuild_position_index([updated_task1, task3])
        assert manager.get_position(1) == 0
        assert manager.get_position(3) == 1

    def test_large_number_of_tasks(self):
        """Test manager handles large number of tasks efficiently."""
        large_task_list = [
            Task(id=i, name=f"Task {i}", priority=1) for i in range(1000)
        ]
        manager = TaskIndexManager(large_task_list)

        # Should handle lookup efficiently
        assert manager.get_by_id(500).name == "Task 500"
        assert manager.get_position(750) == 750  # Position matches index in list
        assert manager.has_task(999) is True

    def test_get_by_ids_with_duplicates(self):
        """Test get_by_ids handles duplicate IDs correctly."""
        manager = TaskIndexManager(self.tasks)

        result = manager.get_by_ids([1, 1, 2, 2, 3])

        # Should contain each task once
        assert len(result) == 3
        assert result[1] == self.task1
        assert result[2] == self.task2
        assert result[3] == self.task3
