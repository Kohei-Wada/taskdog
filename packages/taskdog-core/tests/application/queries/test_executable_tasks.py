from datetime import datetime

from taskdog_core.application.queries.task_query_service import TaskQueryService
from taskdog_core.domain.entities.task import Task, TaskStatus


class _StubRepo:
    """Minimal repository: get_filtered returns all tasks (filters applied in Python)."""

    def __init__(self, tasks):
        self._tasks = tasks

    def get_filtered(self, **kwargs):
        return list(self._tasks)


class _FixedTime:
    def now(self):
        return datetime(2026, 7, 18, 9, 0, 0)


def _task(
    task_id,
    status,
    deadline=None,
    priority=1,
    est=None,
    deps=None,
    is_archived=False,
    tags=None,
):
    return Task(
        id=task_id,
        name=f"t{task_id}",
        priority=priority,
        status=status,
        deadline=deadline,
        estimated_duration=est,
        depends_on=deps or [],
        is_archived=is_archived,
        tags=tags or [],
    )


def _svc(tasks):
    return TaskQueryService(_StubRepo(tasks), _FixedTime())


def test_blocked_by_incomplete_dependency_is_excluded():
    tasks = [
        _task(1, TaskStatus.PENDING),  # dep target, not completed
        _task(2, TaskStatus.PENDING, deps=[1]),  # blocked
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks()]
    assert ids == [1]


def test_completed_dependency_unblocks():
    tasks = [
        _task(1, TaskStatus.COMPLETED),
        _task(2, TaskStatus.PENDING, deps=[1]),
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks()]
    assert ids == [2]  # completed dep-target is not itself executable


def test_missing_dependency_target_excludes_task():
    tasks = [_task(2, TaskStatus.PENDING, deps=[99])]
    assert _svc(tasks).get_executable_tasks() == []


def test_in_progress_ranks_before_pending():
    tasks = [
        _task(1, TaskStatus.PENDING, deadline=datetime(2026, 7, 19)),
        _task(2, TaskStatus.IN_PROGRESS, deadline=datetime(2026, 7, 25)),
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks()]
    assert ids == [2, 1]  # in-progress first despite later deadline


def test_ranking_precedence_within_tier():
    tasks = [
        _task(1, TaskStatus.PENDING, deadline=None, priority=9),
        _task(2, TaskStatus.PENDING, deadline=datetime(2026, 7, 20), priority=1),
        _task(3, TaskStatus.PENDING, deadline=datetime(2026, 7, 19), priority=1),
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks()]
    assert ids == [3, 2, 1]  # earliest deadline first; None-deadline last


def test_limit_caps_results():
    tasks = [_task(i, TaskStatus.PENDING) for i in range(1, 6)]
    assert len(_svc(tasks).get_executable_tasks(limit=2)) == 2


def test_archived_completed_dependency_stays_executable():
    tasks = [
        _task(1, TaskStatus.COMPLETED, is_archived=True),
        _task(2, TaskStatus.PENDING, deps=[1]),
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks()]
    assert ids == [2]  # archived-but-completed dep still satisfies the dependent


def test_archived_task_is_not_returned():
    tasks = [
        _task(1, TaskStatus.PENDING, is_archived=True),
        _task(2, TaskStatus.PENDING),
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks()]
    assert ids == [2]


def test_tags_filter_restricts_candidates():
    tasks = [
        _task(1, TaskStatus.PENDING, tags=["work"]),
        _task(2, TaskStatus.PENDING, tags=["home"]),
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks(tags=["work"])]
    assert ids == [1]


def test_estimate_tie_break():
    tasks = [
        _task(1, TaskStatus.PENDING, est=None),
        _task(2, TaskStatus.PENDING, est=3.0),
        _task(3, TaskStatus.PENDING, est=1.0),
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks()]
    assert ids == [3, 2, 1]  # shorter estimate first; None-estimate last


def test_id_tie_break():
    tasks = [
        _task(3, TaskStatus.PENDING),
        _task(1, TaskStatus.PENDING),
        _task(2, TaskStatus.PENDING),
    ]
    ids = [t.id for t in _svc(tasks).get_executable_tasks()]
    assert ids == [1, 2, 3]
