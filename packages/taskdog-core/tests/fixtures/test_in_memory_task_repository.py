"""Tests for InMemoryTaskRepository.

Validates that the in-memory implementation correctly implements the
TaskRepository interface with proper deepcopy isolation, filtering,
tag operations, and daily allocation methods.
"""

from datetime import date, datetime

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.tag_exceptions import TagNotFoundException

from .repositories import InMemoryTaskRepository


@pytest.fixture
def repo():
    r = InMemoryTaskRepository()
    yield r
    r.clear()


# =============================================================================
# CRUD Operations
# =============================================================================


class TestCreate:
    def test_create_assigns_id(self, repo):
        task = repo.create("Task 1")
        assert task.id is not None
        assert task.id == 1

    def test_create_auto_increments(self, repo):
        t1 = repo.create("Task 1")
        t2 = repo.create("Task 2")
        assert t2.id == t1.id + 1

    def test_create_with_priority(self, repo):
        task = repo.create("Task", priority=5)
        assert task.priority == 5

    def test_create_with_kwargs(self, repo):
        task = repo.create(
            "Task",
            tags=["dev"],
            estimated_duration=2.0,
            is_fixed=True,
        )
        assert task.tags == ["dev"]
        assert task.estimated_duration == 2.0
        assert task.is_fixed is True

    def test_create_sets_timestamps(self, repo):
        task = repo.create("Task")
        assert task.created_at is not None
        assert task.updated_at is not None


class TestGetById:
    def test_returns_task(self, repo):
        created = repo.create("Task 1")
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Task 1"

    def test_returns_none_for_missing(self, repo):
        assert repo.get_by_id(999) is None


class TestGetByIds:
    def test_returns_matching_tasks(self, repo):
        t1 = repo.create("Task 1")
        t2 = repo.create("Task 2")
        repo.create("Task 3")
        result = repo.get_by_ids([t1.id, t2.id])
        assert set(result.keys()) == {t1.id, t2.id}

    def test_skips_missing_ids(self, repo):
        t1 = repo.create("Task 1")
        result = repo.get_by_ids([t1.id, 999])
        assert list(result.keys()) == [t1.id]

    def test_empty_list(self, repo):
        assert repo.get_by_ids([]) == {}


class TestSave:
    def test_save_new_task_assigns_id(self, repo):
        task = Task(name="Test")
        assert task.id is None
        repo.save(task)
        assert task.id is not None

    def test_save_updates_existing(self, repo):
        task = repo.create("Original")
        task.name = "Updated"
        repo.save(task)
        fetched = repo.get_by_id(task.id)
        assert fetched.name == "Updated"

    def test_save_all(self, repo):
        tasks = [Task(name="A"), Task(name="B")]
        repo.save_all(tasks)
        assert len(repo.get_all()) == 2


class TestDelete:
    def test_delete_removes_task(self, repo):
        task = repo.create("Task 1")
        repo.delete(task.id)
        assert repo.get_by_id(task.id) is None

    def test_delete_nonexistent_is_noop(self, repo):
        repo.delete(999)  # Should not raise

    def test_get_all_after_delete(self, repo):
        t1 = repo.create("Task 1")
        repo.create("Task 2")
        repo.delete(t1.id)
        assert len(repo.get_all()) == 1


# =============================================================================
# Deepcopy Isolation
# =============================================================================


class TestDeepcopyIsolation:
    def test_get_by_id_returns_copy(self, repo):
        repo.create("Task 1")
        fetched = repo.get_by_id(1)
        fetched.name = "Modified"
        original = repo.get_by_id(1)
        assert original.name == "Task 1"

    def test_get_all_returns_copies(self, repo):
        repo.create("Task 1")
        tasks = repo.get_all()
        tasks[0].name = "Modified"
        assert repo.get_by_id(1).name == "Task 1"

    def test_save_stores_copy(self, repo):
        task = Task(name="Original")
        repo.save(task)
        task.name = "Changed outside"
        stored = repo.get_by_id(task.id)
        assert stored.name == "Original"

    def test_create_returns_copy(self, repo):
        created = repo.create("Task 1")
        created.name = "Mutated"
        stored = repo.get_by_id(1)
        assert stored.name == "Task 1"


# =============================================================================
# get_filtered
# =============================================================================


class TestGetFiltered:
    def test_no_filters_returns_all(self, repo):
        repo.create("Task 1")
        repo.create("Task 2")
        assert len(repo.get_filtered()) == 2

    def test_exclude_archived(self, repo):
        repo.create("Active")
        repo.create("Archived", is_archived=True)
        result = repo.get_filtered(include_archived=False)
        assert len(result) == 1
        assert result[0].name == "Active"

    def test_include_archived(self, repo):
        repo.create("Active")
        repo.create("Archived", is_archived=True)
        result = repo.get_filtered(include_archived=True)
        assert len(result) == 2

    def test_filter_by_status(self, repo):
        repo.create("Pending")
        t2 = repo.create("Started")
        t2.start(datetime.now())
        repo.save(t2)
        result = repo.get_filtered(status=TaskStatus.IN_PROGRESS)
        assert len(result) == 1
        assert result[0].name == "Started"

    def test_filter_by_tags_or(self, repo):
        repo.create("Tagged A", tags=["a"])
        repo.create("Tagged B", tags=["b"])
        repo.create("No tags")
        result = repo.get_filtered(tags=["a"])
        assert len(result) == 1
        assert result[0].name == "Tagged A"

    def test_filter_by_tags_or_multiple(self, repo):
        repo.create("Tagged A", tags=["a"])
        repo.create("Tagged B", tags=["b"])
        repo.create("No tags")
        result = repo.get_filtered(tags=["a", "b"])
        assert len(result) == 2

    def test_filter_by_tags_and(self, repo):
        repo.create("Has both", tags=["a", "b"])
        repo.create("Only A", tags=["a"])
        result = repo.get_filtered(tags=["a", "b"], match_all_tags=True)
        assert len(result) == 1
        assert result[0].name == "Has both"

    def test_filter_by_date_range(self, repo):
        repo.create("In range", deadline=datetime(2025, 6, 15))
        repo.create("Out of range", deadline=datetime(2025, 1, 1))
        repo.create("No date")
        result = repo.get_filtered(
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 30),
        )
        assert len(result) == 1
        assert result[0].name == "In range"

    def test_filter_by_start_date_only(self, repo):
        repo.create("Future", deadline=datetime(2025, 12, 1))
        repo.create("Past", deadline=datetime(2025, 1, 1))
        result = repo.get_filtered(start_date=date(2025, 6, 1))
        assert len(result) == 1
        assert result[0].name == "Future"

    def test_filter_by_end_date_only(self, repo):
        repo.create("Future", deadline=datetime(2025, 12, 1))
        repo.create("Past", deadline=datetime(2025, 1, 1))
        result = repo.get_filtered(end_date=date(2025, 6, 1))
        assert len(result) == 1
        assert result[0].name == "Past"

    def test_date_filter_checks_multiple_fields(self, repo):
        repo.create("Planned", planned_start=datetime(2025, 6, 15))
        repo.create("Actual", actual_start=datetime(2025, 6, 15))
        result = repo.get_filtered(
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 30),
        )
        assert len(result) == 2

    def test_combined_filters(self, repo):
        repo.create("Match", tags=["dev"], deadline=datetime(2025, 6, 15))
        repo.create("Wrong tag", tags=["ops"], deadline=datetime(2025, 6, 15))
        repo.create("No deadline", tags=["dev"])
        result = repo.get_filtered(
            tags=["dev"],
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 30),
        )
        assert len(result) == 1
        assert result[0].name == "Match"


# =============================================================================
# delete_tag
# =============================================================================


class TestDeleteTag:
    def test_removes_tag_from_tasks(self, repo):
        repo.create("Task 1", tags=["a", "b"])
        repo.create("Task 2", tags=["a"])
        count = repo.delete_tag("a")
        assert count == 2
        t1 = repo.get_by_id(1)
        assert "a" not in t1.tags
        assert "b" in t1.tags
        t2 = repo.get_by_id(2)
        assert t2.tags == []

    def test_raises_for_nonexistent_tag(self, repo):
        with pytest.raises(TagNotFoundException):
            repo.delete_tag("nonexistent")

    def test_tag_tracked_after_create(self, repo):
        repo.create("Task", tags=["tracked"])
        # Should not raise since tag exists
        count = repo.delete_tag("tracked")
        assert count == 1


# =============================================================================
# Daily Allocations
# =============================================================================


class TestDailyAllocations:
    @pytest.fixture
    def repo_with_allocations(self, repo):
        d1 = date(2025, 6, 10)
        d2 = date(2025, 6, 11)
        d3 = date(2025, 6, 12)
        repo.create("Task A", daily_allocations={d1: 2.0, d2: 3.0})
        repo.create("Task B", daily_allocations={d2: 1.0, d3: 4.0})
        return repo

    def test_get_daily_workload_totals(self, repo_with_allocations):
        totals = repo_with_allocations.get_daily_workload_totals(
            start_date=date(2025, 6, 10),
            end_date=date(2025, 6, 12),
        )
        assert totals[date(2025, 6, 10)] == 2.0
        assert totals[date(2025, 6, 11)] == 4.0  # 3.0 + 1.0
        assert totals[date(2025, 6, 12)] == 4.0

    def test_get_daily_workload_totals_with_task_ids(self, repo_with_allocations):
        totals = repo_with_allocations.get_daily_workload_totals(
            start_date=date(2025, 6, 10),
            end_date=date(2025, 6, 12),
            task_ids=[1],
        )
        assert totals.get(date(2025, 6, 10)) == 2.0
        assert totals.get(date(2025, 6, 11)) == 3.0
        assert date(2025, 6, 12) not in totals

    def test_get_daily_allocations_for_tasks(self, repo_with_allocations):
        result = repo_with_allocations.get_daily_allocations_for_tasks(
            task_ids=[1, 2],
        )
        assert 1 in result
        assert 2 in result
        assert result[1][date(2025, 6, 10)] == 2.0

    def test_get_daily_allocations_for_tasks_with_date_filter(
        self, repo_with_allocations
    ):
        result = repo_with_allocations.get_daily_allocations_for_tasks(
            task_ids=[1],
            start_date=date(2025, 6, 11),
            end_date=date(2025, 6, 11),
        )
        assert result[1] == {date(2025, 6, 11): 3.0}

    def test_get_aggregated_daily_allocations(self, repo_with_allocations):
        totals = repo_with_allocations.get_aggregated_daily_allocations(
            task_ids=[1, 2],
        )
        assert totals[date(2025, 6, 11)] == 4.0

    def test_get_aggregated_daily_allocations_subset(self, repo_with_allocations):
        totals = repo_with_allocations.get_aggregated_daily_allocations(
            task_ids=[2],
        )
        assert date(2025, 6, 10) not in totals
        assert totals[date(2025, 6, 11)] == 1.0


# =============================================================================
# Clear
# =============================================================================


class TestClear:
    def test_clear_removes_all_tasks(self, repo):
        repo.create("Task 1")
        repo.create("Task 2")
        repo.clear()
        assert repo.get_all() == []

    def test_clear_resets_id_counter(self, repo):
        repo.create("Task 1")
        repo.clear()
        task = repo.create("After clear")
        assert task.id == 1

    def test_clear_resets_tags(self, repo):
        repo.create("Task", tags=["tag1"])
        repo.clear()
        with pytest.raises(TagNotFoundException):
            repo.delete_tag("tag1")


# =============================================================================
# count_tasks (inherited, uses get_filtered)
# =============================================================================


class TestCountTasks:
    def test_count_all(self, repo):
        repo.create("A")
        repo.create("B")
        assert repo.count_tasks() == 2

    def test_count_with_status_filter(self, repo):
        repo.create("Pending")
        t2 = repo.create("Started")
        t2.start(datetime.now())
        repo.save(t2)
        assert repo.count_tasks(status=TaskStatus.IN_PROGRESS) == 1

    def test_count_tasks_with_tags(self, repo):
        repo.create("Tagged", tags=["dev"])
        repo.create("No tags")
        assert repo.count_tasks_with_tags() == 1
