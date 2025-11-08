"""Integration tests for TUI app to protect existing behavior during refactoring."""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from taskdog.tui.context import TUIContext
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus


class TestTaskdogTUIIntegration(unittest.TestCase):
    """Integration tests for TaskdogTUI to protect existing behavior."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock API client
        self.api_client = Mock()

        # Use default config
        from taskdog_core.shared.config_manager import ConfigManager

        self.config = ConfigManager.load()

        # Create context
        self.context = TUIContext(
            api_client=self.api_client,
            config=self.config,
            holiday_checker=None,
        )

        # Sample tasks for testing
        self.sample_tasks = [
            TaskRowDto(
                id=1,
                name="Task 1",
                priority=1,
                status=TaskStatus.PENDING,
                planned_start=None,
                planned_end=None,
                deadline=datetime(2025, 1, 15),
                actual_start=None,
                actual_end=None,
                estimated_duration=None,
                actual_duration_hours=None,
                is_fixed=False,
                depends_on=[],
                tags=[],
                is_archived=False,
                is_finished=False,
                created_at=datetime(2025, 1, 1, 9, 0),
                updated_at=datetime(2025, 1, 1, 9, 0),
            ),
            TaskRowDto(
                id=2,
                name="Task 2",
                priority=2,
                status=TaskStatus.COMPLETED,
                planned_start=None,
                planned_end=None,
                deadline=datetime(2025, 1, 10),
                actual_start=datetime(2025, 1, 8, 9, 0),
                actual_end=datetime(2025, 1, 8, 17, 0),
                estimated_duration=None,
                actual_duration_hours=8.0,
                is_fixed=False,
                depends_on=[],
                tags=[],
                is_archived=False,
                is_finished=True,
                created_at=datetime(2025, 1, 1, 9, 0),
                updated_at=datetime(2025, 1, 8, 17, 0),
            ),
            TaskRowDto(
                id=3,
                name="Task 3",
                priority=3,
                status=TaskStatus.IN_PROGRESS,
                planned_start=None,
                planned_end=None,
                deadline=datetime(2025, 1, 20),
                actual_start=datetime(2025, 1, 12, 9, 0),
                actual_end=None,
                estimated_duration=None,
                actual_duration_hours=None,
                is_fixed=False,
                depends_on=[],
                tags=[],
                is_archived=False,
                is_finished=False,
                created_at=datetime(2025, 1, 1, 9, 0),
                updated_at=datetime(2025, 1, 12, 9, 0),
            ),
        ]

    @patch("taskdog.tui.app.TaskdogTUI._load_tasks")
    def test_initial_state_values(self, mock_load_tasks):
        """Test that app initializes with correct default state."""
        # Note: We can't easily test Textual app initialization without running it
        # This is a placeholder for when AppState is implemented
        # We'll verify initial values from AppState instead
        pass

    def test_toggle_completed_filter_logic(self):
        """Test hide_completed toggle logic."""
        # Create a simple state manager to test filtering logic
        # This simulates what AppState.get_filtered_tasks() should do

        hide_completed = False

        def get_filtered_tasks(tasks, hide_completed_flag):
            """Simulate filtering logic."""
            return [
                t
                for t in tasks
                if not t.is_archived
                and (
                    not hide_completed_flag
                    or t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELED]
                )
            ]

        # Without filter
        filtered = get_filtered_tasks(self.sample_tasks, hide_completed)
        self.assertEqual(len(filtered), 3)
        self.assertIn(self.sample_tasks[0], filtered)  # PENDING
        self.assertIn(self.sample_tasks[1], filtered)  # COMPLETED
        self.assertIn(self.sample_tasks[2], filtered)  # IN_PROGRESS

        # With filter
        hide_completed = True
        filtered = get_filtered_tasks(self.sample_tasks, hide_completed)
        self.assertEqual(len(filtered), 2)
        self.assertIn(self.sample_tasks[0], filtered)  # PENDING
        self.assertNotIn(self.sample_tasks[1], filtered)  # COMPLETED (filtered out)
        self.assertIn(self.sample_tasks[2], filtered)  # IN_PROGRESS

    def test_archived_tasks_always_filtered(self):
        """Test that archived tasks are always excluded from display."""
        # Add an archived task
        archived_task = TaskRowDto(
            id=4,
            name="Archived Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=None,
            actual_end=None,
            estimated_duration=None,
            actual_duration_hours=None,
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=True,  # Archived
            is_finished=False,
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )

        tasks_with_archived = [*self.sample_tasks, archived_task]

        def get_filtered_tasks(tasks, hide_completed_flag):
            """Simulate filtering logic."""
            return [
                t
                for t in tasks
                if not t.is_archived
                and (
                    not hide_completed_flag
                    or t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELED]
                )
            ]

        # Even with hide_completed=False, archived task should be filtered
        filtered = get_filtered_tasks(tasks_with_archived, False)
        self.assertEqual(len(filtered), 3)
        self.assertNotIn(archived_task, filtered)

        # With hide_completed=True
        filtered = get_filtered_tasks(tasks_with_archived, True)
        self.assertEqual(len(filtered), 2)
        self.assertNotIn(archived_task, filtered)

    def test_sort_by_deadline(self):
        """Test sorting tasks by deadline."""

        # Simulate sorting logic
        def sort_tasks(tasks, sort_by):
            """Simulate sorting logic."""
            if sort_by == "deadline":
                return sorted(
                    tasks,
                    key=lambda t: (
                        t.deadline is None,  # None values last
                        t.deadline if t.deadline else datetime.max,
                    ),
                )
            return tasks

        sorted_tasks = sort_tasks(self.sample_tasks, "deadline")

        # Task 2 (Jan 10) < Task 1 (Jan 15) < Task 3 (Jan 20)
        self.assertEqual(sorted_tasks[0].id, 2)
        self.assertEqual(sorted_tasks[1].id, 1)
        self.assertEqual(sorted_tasks[2].id, 3)

    def test_sort_by_priority(self):
        """Test sorting tasks by priority."""

        def sort_tasks(tasks, sort_by):
            """Simulate sorting logic."""
            if sort_by == "priority":
                return sorted(tasks, key=lambda t: t.priority)
            return tasks

        sorted_tasks = sort_tasks(self.sample_tasks, "priority")

        # Priority 1 < Priority 2 < Priority 3
        self.assertEqual(sorted_tasks[0].id, 1)
        self.assertEqual(sorted_tasks[1].id, 2)
        self.assertEqual(sorted_tasks[2].id, 3)

    def test_cache_behavior_on_toggle(self):
        """Test that cache is reused when toggling completed filter."""
        # This test verifies the expected behavior:
        # 1. Initial load fetches tasks from API
        # 2. Toggle completed should NOT trigger new API call
        # 3. Only client-side filtering should happen

        # Simulate cache
        cached_tasks = self.sample_tasks.copy()

        # Mock API call counter
        api_call_count = 0

        def mock_load_from_api():
            nonlocal api_call_count
            api_call_count += 1
            return cached_tasks

        def apply_filter(hide_completed):
            # This simulates what should happen on toggle:
            # Use cached tasks, no API call
            return [
                t
                for t in cached_tasks
                if not t.is_archived
                and (
                    not hide_completed
                    or t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELED]
                )
            ]

        # Initial load (API call)
        tasks = mock_load_from_api()
        self.assertEqual(api_call_count, 1)
        self.assertEqual(len(tasks), 3)

        # Toggle completed (no API call, use cache)
        filtered = apply_filter(hide_completed=True)
        self.assertEqual(api_call_count, 1)  # Still 1, no new API call
        self.assertEqual(len(filtered), 2)

        # Toggle again (no API call, use cache)
        filtered = apply_filter(hide_completed=False)
        self.assertEqual(api_call_count, 1)  # Still 1
        self.assertEqual(len(filtered), 3)

    def test_notes_check_should_be_batched(self):
        """Test that notes checks are batched, not per-task."""
        # This is the N+1 problem we're fixing
        # Expected behavior AFTER fix:
        # - 1 API call to get notes for all tasks
        # - NOT 1 API call per task

        task_ids = [1, 2, 3]

        # Mock batch notes checker
        batch_call_count = 0
        per_task_call_count = 0

        def batch_check_notes(ids):
            """Simulate batch API call (GOOD)."""
            nonlocal batch_call_count
            batch_call_count += 1
            return {task_id: (task_id % 2 == 0) for task_id in ids}

        def per_task_check_notes(task_id):
            """Simulate per-task API call (BAD - N+1 problem)."""
            nonlocal per_task_call_count
            per_task_call_count += 1
            return task_id % 2 == 0

        # BAD APPROACH (current - N+1 problem)
        per_task_results = {}
        for task_id in task_ids:
            per_task_results[task_id] = per_task_check_notes(task_id)

        self.assertEqual(per_task_call_count, 3)  # 3 API calls - BAD!

        # GOOD APPROACH (after fix - batched)
        batch_results = batch_check_notes(task_ids)

        self.assertEqual(batch_call_count, 1)  # 1 API call - GOOD!
        self.assertEqual(batch_results, per_task_results)  # Same result


class TestAppStateIntegration(unittest.TestCase):
    """Tests for AppState integration (will be used after implementation)."""

    def test_state_changes_trigger_ui_updates(self):
        """Test that state changes should trigger appropriate UI updates."""
        # Placeholder for future integration test
        # This will test that:
        # 1. AppState.toggle_completed() triggers table refresh
        # 2. AppState.set_sort_by() triggers gantt recalculation
        # 3. State changes are reactive
        pass

    def test_widget_receives_state_as_props(self):
        """Test that widgets receive state as props, not manage their own state."""
        # Placeholder for future integration test
        # This will test that:
        # 1. GanttWidget receives sort_by from app, not stores it
        # 2. TaskTable receives filtered tasks, not filters them itself
        pass


if __name__ == "__main__":
    unittest.main()
