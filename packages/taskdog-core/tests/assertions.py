"""
Custom assertion helpers for taskdog-core tests.

This module provides domain-specific assertions to improve test readability
and reduce repeated assertion patterns.
"""

from datetime import datetime

from taskdog_core.domain.entities.task import Task, TaskStatus


def assert_task_has_status(task: Task, expected_status: TaskStatus, message: str = ""):
    """Assert that a task has the expected status.

    Args:
        task: Task to check
        expected_status: Expected TaskStatus
        message: Optional custom error message

    Raises:
        AssertionError: If task status doesn't match expected

    Example:
        assert_task_has_status(task, TaskStatus.IN_PROGRESS)
    """
    if not message:
        message = f"Expected task status {expected_status}, got {task.status}"
    assert task.status == expected_status, message


def assert_task_has_timestamps(
    task: Task,
    actual_start: datetime | None = None,
    actual_end: datetime | None = None,
):
    """Assert that a task has expected actual_start and actual_end timestamps.

    Args:
        task: Task to check
        actual_start: Expected actual_start (None to check it's None)
        actual_end: Expected actual_end (None to check it's None)

    Raises:
        AssertionError: If timestamps don't match expected values

    Example:
        # Check task was started
        assert_task_has_timestamps(task, actual_start=start_time, actual_end=None)

        # Check task was completed
        assert_task_has_timestamps(task, actual_start=start_time, actual_end=end_time)

        # Check task was reset
        assert_task_has_timestamps(task, actual_start=None, actual_end=None)
    """
    if actual_start is not None:
        assert (
            task.actual_start == actual_start
        ), f"Expected actual_start={actual_start}, got {task.actual_start}"
    else:
        assert (
            task.actual_start is None
        ), f"Expected actual_start=None, got {task.actual_start}"

    if actual_end is not None:
        assert (
            task.actual_end == actual_end
        ), f"Expected actual_end={actual_end}, got {task.actual_end}"
    else:
        assert (
            task.actual_end is None
        ), f"Expected actual_end=None, got {task.actual_end}"


def assert_task_scheduled(
    task: Task,
    expected_start: datetime,
    expected_end: datetime,
    message: str = "",
):
    """Assert that a task is scheduled with expected planned dates.

    Args:
        task: Task to check
        expected_start: Expected planned_start
        expected_end: Expected planned_end
        message: Optional custom error message

    Raises:
        AssertionError: If planned dates don't match

    Example:
        assert_task_scheduled(
            task,
            datetime(2025, 1, 15, 9, 0),
            datetime(2025, 1, 15, 17, 0)
        )
    """
    if not message:
        message = (
            f"Expected task scheduled {expected_start} to {expected_end}, "
            f"got {task.planned_start} to {task.planned_end}"
        )
    assert task.planned_start == expected_start, message
    assert task.planned_end == expected_end, message


def assert_task_has_allocations(
    task: Task, expected_allocations: dict[str, float], message: str = ""
):
    """Assert that a task has expected daily_allocations.

    Args:
        task: Task to check
        expected_allocations: Expected daily_allocations dict
        message: Optional custom error message

    Raises:
        AssertionError: If allocations don't match

    Example:
        assert_task_has_allocations(
            task,
            {"2025-01-15": 4.0, "2025-01-16": 4.0}
        )
    """
    if not message:
        message = (
            f"Expected allocations {expected_allocations}, "
            f"got {task.daily_allocations}"
        )
    assert task.daily_allocations == expected_allocations, message


def assert_total_allocated_hours(task: Task, expected_total: float, message: str = ""):
    """Assert that sum of daily_allocations equals expected total.

    Args:
        task: Task to check
        expected_total: Expected sum of allocated hours
        message: Optional custom error message

    Raises:
        AssertionError: If total doesn't match

    Example:
        assert_total_allocated_hours(task, 8.0)
    """
    total = (
        0.0 if task.daily_allocations is None else sum(task.daily_allocations.values())
    )

    if not message:
        message = f"Expected total allocated hours {expected_total}, got {total}"
    assert total == expected_total, message


def assert_task_has_dependencies(
    task: Task, expected_deps: list[int], message: str = ""
):
    """Assert that a task has expected dependencies.

    Args:
        task: Task to check
        expected_deps: Expected list of dependency IDs
        message: Optional custom error message

    Raises:
        AssertionError: If dependencies don't match

    Example:
        assert_task_has_dependencies(task, [1, 2, 3])
        assert_task_has_dependencies(task, [])  # no dependencies
    """
    if not message:
        message = f"Expected depends_on={expected_deps}, got {task.depends_on}"
    assert task.depends_on == expected_deps, message


def assert_task_has_tags(task: Task, expected_tags: list[str], message: str = ""):
    """Assert that a task has expected tags.

    Args:
        task: Task to check
        expected_tags: Expected list of tags (order-sensitive)
        message: Optional custom error message

    Raises:
        AssertionError: If tags don't match

    Example:
        assert_task_has_tags(task, ["urgent", "backend"])
    """
    if not message:
        message = f"Expected tags={expected_tags}, got {task.tags}"
    assert task.tags == expected_tags, message


def assert_task_is_archived(task: Task, expected: bool = True, message: str = ""):
    """Assert that a task's archived status matches expected.

    Args:
        task: Task to check
        expected: Expected is_archived value (default: True)
        message: Optional custom error message

    Raises:
        AssertionError: If archived status doesn't match

    Example:
        assert_task_is_archived(task)  # check it's archived
        assert_task_is_archived(task, False)  # check it's not archived
    """
    if not message:
        message = f"Expected is_archived={expected}, got {task.is_archived}"
    assert task.is_archived == expected, message


def assert_task_is_fixed(task: Task, expected: bool = True, message: str = ""):
    """Assert that a task's fixed status matches expected.

    Args:
        task: Task to check
        expected: Expected is_fixed value (default: True)
        message: Optional custom error message

    Raises:
        AssertionError: If fixed status doesn't match

    Example:
        assert_task_is_fixed(task)  # check it's fixed
        assert_task_is_fixed(task, False)  # check it's not fixed
    """
    if not message:
        message = f"Expected is_fixed={expected}, got {task.is_fixed}"
    assert task.is_fixed == expected, message
