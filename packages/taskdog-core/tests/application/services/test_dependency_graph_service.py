"""Tests for DependencyGraphService."""

import pytest

from taskdog_core.application.services.dependency_graph_service import (
    DependencyGraphService,
)


class TestDependencyGraphService:
    """Test cases for DependencyGraphService."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Set up test fixtures."""
        self.repository = repository
        self.service = DependencyGraphService(self.repository)

    def test_detect_cycle_no_cycle_returns_none(self):
        """Test detect_cycle returns None when no cycle exists."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        # No dependencies at all
        result = self.service.detect_cycle(task1.id, task2.id)

        assert result is None

    def test_detect_cycle_direct_cycle(self):
        """Test detect_cycle detects direct cycle (A→B, B→A)."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        # task1 depends on task2
        task1.depends_on = [task2.id]
        self.repository.save(task1)

        # Try to make task2 depend on task1 (would create cycle 2→1→2)
        result = self.service.detect_cycle(task2.id, task1.id)

        assert result is not None
        assert result == [task1.id, task2.id]

    def test_detect_cycle_indirect_three_node_cycle(self):
        """Test detect_cycle detects 3-node cycle (A→B→C, C→A)."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)

        # Create chain: 1→2→3
        task1.depends_on = [task2.id]
        self.repository.save(task1)
        task2.depends_on = [task3.id]
        self.repository.save(task2)

        # Try to make task3 depend on task1 (would create 3→1→2→3)
        result = self.service.detect_cycle(task3.id, task1.id)

        assert result is not None
        assert result == [task1.id, task2.id, task3.id]

    def test_detect_cycle_long_chain_cycle(self):
        """Test detect_cycle detects cycle in long dependency chain."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)
        task5 = self.repository.create(name="Task 5", priority=1)

        # Create chain: 1→2→3→4→5
        task1.depends_on = [task2.id]
        self.repository.save(task1)
        task2.depends_on = [task3.id]
        self.repository.save(task2)
        task3.depends_on = [task4.id]
        self.repository.save(task3)
        task4.depends_on = [task5.id]
        self.repository.save(task4)

        # Try to make task5 depend on task1 (would create 5→1→2→3→4→5)
        result = self.service.detect_cycle(task5.id, task1.id)

        assert result is not None
        assert result == [task1.id, task2.id, task3.id, task4.id, task5.id]

    def test_detect_cycle_allows_diamond_pattern(self):
        """Test detect_cycle allows diamond pattern (A→B,C; B,C→D)."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)

        # Create diamond: 1→2, 1→3, 2→4, 3→4
        task1.depends_on = [task2.id, task3.id]
        self.repository.save(task1)
        task2.depends_on = [task4.id]
        self.repository.save(task2)
        task3.depends_on = [task4.id]
        self.repository.save(task3)

        # This should not create a cycle
        result = self.service.detect_cycle(task1.id, task2.id)

        assert result is None

    def test_detect_cycle_allows_parallel_chains(self):
        """Test detect_cycle allows parallel independent chains."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)

        # Create two independent chains: 1→2, 3→4
        task1.depends_on = [task2.id]
        self.repository.save(task1)
        task3.depends_on = [task4.id]
        self.repository.save(task3)

        # Connecting chains should be fine if no cycle
        result = self.service.detect_cycle(task1.id, task3.id)

        assert result is None

    def test_detect_cycle_self_loop(self):
        """Test detect_cycle detects self-loop (A→A)."""
        task1 = self.repository.create(name="Task 1", priority=1)

        # Try to make task1 depend on itself
        result = self.service.detect_cycle(task1.id, task1.id)

        assert result is not None
        assert result == [task1.id]

    def test_detect_cycle_cycle_in_middle_of_chain(self):
        """Test detect_cycle detects cycle connecting to middle of chain."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)

        # Create chain: 1→2→3
        task1.depends_on = [task2.id]
        self.repository.save(task1)
        task2.depends_on = [task3.id]
        self.repository.save(task2)

        # Try to make task3 depend on task2 (would create 3→2→3)
        result = self.service.detect_cycle(task3.id, task2.id)

        assert result is not None
        assert result == [task2.id, task3.id]

    def test_detect_cycle_with_multiple_dependencies(self):
        """Test detect_cycle with task having multiple dependencies."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)

        # task1 depends on both task2 and task3
        # task2 depends on task4
        # task3 depends on task4
        task1.depends_on = [task2.id, task3.id]
        self.repository.save(task1)
        task2.depends_on = [task4.id]
        self.repository.save(task2)
        task3.depends_on = [task4.id]
        self.repository.save(task3)

        # Try to make task4 depend on task1 (would create cycle)
        result = self.service.detect_cycle(task4.id, task1.id)

        assert result is not None
        # Cycle should be detected through one of the paths
        assert task1.id in result
        assert task4.id in result

    def test_detect_cycle_visited_node_optimization(self):
        """Test that visited nodes are not re-explored."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)

        # Create convergent paths: 1→2→4, 1→3→4
        task1.depends_on = [task2.id, task3.id]
        self.repository.save(task1)
        task2.depends_on = [task4.id]
        self.repository.save(task2)
        task3.depends_on = [task4.id]
        self.repository.save(task3)

        # Adding task5 that doesn't create cycle
        task5 = self.repository.create(name="Task 5", priority=1)
        result = self.service.detect_cycle(task4.id, task5.id)

        assert result is None

    def test_detect_cycle_with_nonexistent_dependency(self):
        """Test detect_cycle handles nonexistent dependency gracefully."""
        task1 = self.repository.create(name="Task 1", priority=1)

        # Task depends on non-existent task
        task1.depends_on = [999]
        self.repository.save(task1)

        # Should not crash, should return None (no cycle found)
        result = self.service.detect_cycle(task1.id, 998)

        assert result is None

    def test_detect_cycle_empty_depends_on(self):
        """Test detect_cycle with task having empty depends_on."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        # task1 has empty depends_on
        task1.depends_on = []
        self.repository.save(task1)

        result = self.service.detect_cycle(task2.id, task1.id)

        assert result is None

    def test_detect_cycle_complex_graph_with_cycle(self):
        """Test detect_cycle in complex graph with multiple branches."""
        # Create complex graph:
        # 1→2, 1→3, 2→4, 3→4, 4→5, 5→6
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)
        task4 = self.repository.create(name="Task 4", priority=1)
        task5 = self.repository.create(name="Task 5", priority=1)
        task6 = self.repository.create(name="Task 6", priority=1)

        task1.depends_on = [task2.id, task3.id]
        self.repository.save(task1)
        task2.depends_on = [task4.id]
        self.repository.save(task2)
        task3.depends_on = [task4.id]
        self.repository.save(task3)
        task4.depends_on = [task5.id]
        self.repository.save(task4)
        task5.depends_on = [task6.id]
        self.repository.save(task5)

        # Try to make task6 depend on task3 (creates cycle through convergent paths)
        result = self.service.detect_cycle(task6.id, task3.id)

        assert result is not None
        assert task3.id in result
        assert task6.id in result
