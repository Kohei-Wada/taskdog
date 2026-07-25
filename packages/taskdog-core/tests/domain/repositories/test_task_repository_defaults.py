"""Tests for TaskRepository's default (non-overridden) filtering methods."""

from datetime import date, datetime
from typing import Any

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.repositories.task_repository import TaskRepository


class MinimalTaskRepository(TaskRepository):
    """Repository that only implements the abstract methods.

    It deliberately does not override get_filtered()/count_tasks(), so it
    exercises the default implementations provided by the base class.
    """

    def __init__(self, tasks: list[Task]) -> None:
        self._tasks = tasks

    def get_all(self) -> list[Task]:
        return list(self._tasks)

    def get_by_id(self, task_id: int) -> Task | None:
        return next((t for t in self._tasks if t.id == task_id), None)

    def get_by_ids(self, task_ids: list[int]) -> dict[int, Task]:
        return {t.id: t for t in self._tasks if t.id in task_ids}

    def save(self, task: Task) -> None:
        self._tasks.append(task)

    def save_all(self, tasks: list[Task]) -> None:
        self._tasks.extend(tasks)

    def delete(self, task_id: int) -> None:
        self._tasks = [t for t in self._tasks if t.id != task_id]

    def create(self, name: str, priority: int | None = None, **kwargs: Any) -> Task:
        raise NotImplementedError


@pytest.fixture
def repository() -> MinimalTaskRepository:
    now = datetime(2026, 1, 1)
    return MinimalTaskRepository(
        [
            Task(
                id=1,
                name="active",
                created_at=now,
                updated_at=now,
                tags=["work"],
                deadline=datetime(2026, 3, 10),
            ),
            Task(
                id=2,
                name="archived",
                created_at=now,
                updated_at=now,
                is_archived=True,
            ),
            Task(
                id=3,
                name="completed",
                created_at=now,
                updated_at=now,
                status=TaskStatus.COMPLETED,
                tags=["home"],
                deadline=datetime(2026, 6, 20),
            ),
        ]
    )


class TestTaskRepositoryDefaultGetFiltered:
    """The default get_filtered() must honour its filter arguments."""

    def test_excludes_archived_tasks(self, repository: MinimalTaskRepository) -> None:
        names = [t.name for t in repository.get_filtered(include_archived=False)]
        assert names == ["active", "completed"]

    def test_filters_by_status(self, repository: MinimalTaskRepository) -> None:
        names = [t.name for t in repository.get_filtered(status=TaskStatus.COMPLETED)]
        assert names == ["completed"]

    def test_filters_by_tags(self, repository: MinimalTaskRepository) -> None:
        names = [t.name for t in repository.get_filtered(tags=["work"])]
        assert names == ["active"]

    def test_filters_by_date_range(self, repository: MinimalTaskRepository) -> None:
        names = [
            t.name
            for t in repository.get_filtered(
                start_date=date(2026, 1, 1), end_date=date(2026, 4, 1)
            )
        ]
        assert names == ["active"]

    def test_no_filters_returns_all_tasks(
        self, repository: MinimalTaskRepository
    ) -> None:
        assert len(repository.get_filtered()) == 3

    def test_count_tasks_uses_filters(self, repository: MinimalTaskRepository) -> None:
        assert repository.count_tasks(include_archived=False) == 2
