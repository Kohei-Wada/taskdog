"""In-memory repository implementations for testing.

These implementations store data in memory and can be easily cleared between tests.
"""

from copy import deepcopy
from datetime import date, datetime
from typing import Any

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.tag_exceptions import TagNotFoundException
from taskdog_core.domain.repositories.task_repository import TaskRepository


class InMemoryTaskRepository(TaskRepository):
    """In-memory task repository for testing.

    Provides a pure Python dict-based storage for tasks that can be
    easily cleared between tests. Uses deepcopy for read/write isolation.
    """

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id: int = 1
        self._tags: set[str] = set()

    def get_all(self) -> list[Task]:
        return [deepcopy(task) for task in self._tasks.values()]

    def get_by_id(self, task_id: int) -> Task | None:
        task = self._tasks.get(task_id)
        return deepcopy(task) if task is not None else None

    def get_by_ids(self, task_ids: list[int]) -> dict[int, Task]:
        return {
            tid: deepcopy(self._tasks[tid]) for tid in task_ids if tid in self._tasks
        }

    def save(self, task: Task) -> None:
        if task.id is None:
            task.id = self._next_id
            self._next_id += 1
        self._tasks[task.id] = deepcopy(task)
        # Track tags
        for tag in task.tags:
            self._tags.add(tag)

    def save_all(self, tasks: list[Task]) -> None:
        for task in tasks:
            self.save(task)

    def delete(self, task_id: int) -> None:
        task = self._tasks.pop(task_id, None)
        if task is not None:
            # Clean up tags that no longer have any tasks
            self._rebuild_tags()

    def create(self, name: str, priority: int | None = None, **kwargs: Any) -> Task:
        now = datetime.now()
        task = Task(
            id=None,
            name=name,
            priority=priority,
            created_at=now,
            updated_at=now,
            **kwargs,
        )
        self.save(task)
        return deepcopy(self._tasks[task.id])

    # -- Overridden default methods --

    def get_filtered(
        self,
        include_archived: bool = True,
        status: TaskStatus | None = None,
        tags: list[str] | None = None,
        match_all_tags: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Task]:
        result: list[Task] = []
        for task in self._tasks.values():
            if not include_archived and task.is_archived:
                continue
            if status is not None and task.status != status:
                continue
            if tags:
                if match_all_tags:
                    if not all(t in task.tags for t in tags):
                        continue
                else:
                    if not any(t in task.tags for t in tags):
                        continue
            if (
                start_date is not None or end_date is not None
            ) and not self._matches_date_filter(task, start_date, end_date):
                continue
            result.append(deepcopy(task))
        return result

    def delete_tag(self, tag_name: str) -> int:
        if tag_name not in self._tags:
            raise TagNotFoundException(tag_name)
        count = 0
        for task in self._tasks.values():
            if tag_name in task.tags:
                task.tags.remove(tag_name)
                count += 1
        self._tags.discard(tag_name)
        return count

    def get_daily_workload_totals(
        self,
        start_date: date,
        end_date: date,
        task_ids: list[int] | None = None,
    ) -> dict[date, float]:
        totals: dict[date, float] = {}
        for tid, task in self._tasks.items():
            if task_ids is not None and tid not in task_ids:
                continue
            for d, hours in task.daily_allocations.items():
                if start_date <= d <= end_date:
                    totals[d] = totals.get(d, 0.0) + hours
        return totals

    def get_daily_allocations_for_tasks(
        self,
        task_ids: list[int],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[int, dict[date, float]]:
        result: dict[int, dict[date, float]] = {}
        for tid in task_ids:
            task = self._tasks.get(tid)
            if task is None:
                continue
            allocations: dict[date, float] = {}
            for d, hours in task.daily_allocations.items():
                if start_date is not None and d < start_date:
                    continue
                if end_date is not None and d > end_date:
                    continue
                allocations[d] = hours
            if allocations:
                result[tid] = allocations
        return result

    def get_aggregated_daily_allocations(
        self,
        task_ids: list[int],
    ) -> dict[date, float]:
        totals: dict[date, float] = {}
        for tid in task_ids:
            task = self._tasks.get(tid)
            if task is None:
                continue
            for d, hours in task.daily_allocations.items():
                totals[d] = totals.get(d, 0.0) + hours
        return totals

    def clear(self) -> None:
        """Clear all data. Used between tests for isolation."""
        self._tasks.clear()
        self._next_id = 1
        self._tags.clear()

    # -- Private helpers --

    def _rebuild_tags(self) -> None:
        """Rebuild the tag set from current tasks."""
        self._tags = set()
        for task in self._tasks.values():
            for tag in task.tags:
                self._tags.add(tag)

    @staticmethod
    def _matches_date_filter(
        task: Task, start_date: date | None, end_date: date | None
    ) -> bool:
        """Check if any of the task's date fields fall within the range.

        Mirrors the SQL date filtering logic: checks deadline, planned_start,
        planned_end, actual_start, actual_end with OR logic.
        """
        date_fields: list[datetime | None] = [
            task.deadline,
            task.planned_start,
            task.planned_end,
            task.actual_start,
            task.actual_end,
        ]
        for dt in date_fields:
            if dt is None:
                continue
            d = dt.date() if isinstance(dt, datetime) else dt
            if start_date is not None and end_date is not None:
                if start_date <= d <= end_date:
                    return True
            elif start_date is not None:
                if d >= start_date:
                    return True
            elif end_date is not None and d <= end_date:
                return True
        return False


class InMemoryNotesRepository:
    """In-memory notes repository for testing.

    Provides a simple dict-based storage for notes that can be cleared between tests.
    """

    def __init__(self):
        self._notes: dict[int, str] = {}

    def has_notes(self, task_id: int) -> bool:
        """Check if task has notes."""
        return task_id in self._notes and len(self._notes[task_id]) > 0

    def read_notes(self, task_id: int) -> str | None:
        """Read notes for task."""
        return self._notes.get(task_id)

    def write_notes(self, task_id: int, content: str) -> None:
        """Write notes for task."""
        self._notes[task_id] = content

    def delete_notes(self, task_id: int) -> None:
        """Delete notes for task."""
        if task_id in self._notes:
            del self._notes[task_id]

    def ensure_notes_dir(self) -> None:
        """No-op for in-memory implementation."""
        pass

    def get_task_ids_with_notes(self, task_ids: list[int]) -> set[int]:
        """Get task IDs that have notes from a list of task IDs."""
        return {task_id for task_id in task_ids if self.has_notes(task_id)}

    def clear(self) -> None:
        """Clear all notes. Used between tests for isolation."""
        self._notes.clear()
