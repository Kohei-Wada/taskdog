import unittest
from datetime import datetime

from parameterized import parameterized

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.services.time_tracker import TimeTracker


class TestTimeTracker(unittest.TestCase):
    """Test cases for TimeTracker"""

    def setUp(self):
        """Create a TimeTracker instance for each test"""
        self.tracker = TimeTracker()

    @parameterized.expand(
        [
            ("in_progress_sets_actual_start", TaskStatus.IN_PROGRESS, "actual_start"),
            ("completed_sets_actual_end", TaskStatus.COMPLETED, "actual_end"),
            ("canceled_sets_actual_end", TaskStatus.CANCELED, "actual_end"),
        ]
    )
    def test_record_time_on_status_change_sets_timestamps(
        self, _scenario, new_status, field_name
    ):
        """Test that appropriate timestamps are recorded for different status changes."""
        task = Task(name="Test Task", priority=1, id=1)
        self.assertIsNone(getattr(task, field_name))

        self.tracker.record_time_on_status_change(task, new_status)

        self.assertIsNotNone(getattr(task, field_name))
        self.assertIsInstance(getattr(task, field_name), datetime)

    def test_no_record_for_pending(self):
        """Test that no timestamps are recorded for PENDING status"""
        task = Task(name="Test Task", priority=1, id=1)

        self.tracker.record_time_on_status_change(task, TaskStatus.PENDING)

        self.assertIsNone(task.actual_start)
        self.assertIsNone(task.actual_end)

    def test_do_not_overwrite_existing_actual_start(self):
        """Test that existing actual_start is not overwritten"""
        original_start = datetime(2025, 1, 1, 10, 0, 0)
        task = Task(name="Test Task", priority=1, id=1, actual_start=original_start)

        self.tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)

        self.assertEqual(task.actual_start, original_start)

    def test_do_not_overwrite_existing_actual_end(self):
        """Test that existing actual_end is not overwritten"""
        original_end = datetime(2025, 1, 1, 18, 0, 0)
        task = Task(name="Test Task", priority=1, id=1, actual_end=original_end)

        self.tracker.record_time_on_status_change(task, TaskStatus.COMPLETED)

        self.assertEqual(task.actual_end, original_end)

    def test_workflow_pending_to_in_progress_to_completed(self):
        """Test a complete workflow: PENDING -> IN_PROGRESS -> COMPLETED"""
        task = Task(name="Test Task", priority=1, id=1, status=TaskStatus.PENDING)

        # Start the task
        self.tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(task.actual_start)
        self.assertIsNone(task.actual_end)

        # Complete the task
        self.tracker.record_time_on_status_change(task, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.actual_start)
        self.assertIsNotNone(task.actual_end)

    def test_workflow_pending_to_completed_without_in_progress(self):
        """Test completing a task without going through IN_PROGRESS"""
        task = Task(name="Test Task", priority=1, id=1, status=TaskStatus.PENDING)

        self.tracker.record_time_on_status_change(task, TaskStatus.COMPLETED)

        # Only actual_end should be set
        self.assertIsNone(task.actual_start)
        self.assertIsNotNone(task.actual_end)

    def test_timestamp_is_datetime_object(self):
        """Test that timestamps are datetime objects"""
        task = Task(name="Test Task", priority=1, id=1)

        self.tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)

        # Should be a datetime object
        self.assertIsInstance(task.actual_start, datetime)

    def test_multiple_status_changes(self):
        """Test multiple status changes don't overwrite original timestamps"""
        task = Task(name="Test Task", priority=1, id=1)

        # First transition: PENDING -> IN_PROGRESS
        self.tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)
        original_start = task.actual_start

        # Second transition: IN_PROGRESS -> PENDING (paused)
        self.tracker.record_time_on_status_change(task, TaskStatus.PENDING)

        # Third transition: PENDING -> IN_PROGRESS (resumed)
        self.tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)

        # Original start time should be preserved
        self.assertEqual(task.actual_start, original_start)

    @parameterized.expand(
        [
            (
                "both_timestamps_set",
                datetime(2025, 1, 1, 10, 0, 0),
                datetime(2025, 1, 1, 18, 0, 0),
            ),
            ("only_actual_start_set", datetime(2025, 1, 1, 10, 0, 0), None),
            ("no_timestamps_set", None, None),
        ]
    )
    def test_clear_time_tracking_handles_all_scenarios(
        self, _scenario, actual_start, actual_end
    ):
        """Test that clear_time_tracking clears timestamps in various scenarios."""
        task = Task(
            name="Test Task",
            priority=1,
            id=1,
            actual_start=actual_start,
            actual_end=actual_end,
        )

        self.tracker.clear_time_tracking(task)

        self.assertIsNone(task.actual_start)
        self.assertIsNone(task.actual_end)


if __name__ == "__main__":
    unittest.main()
