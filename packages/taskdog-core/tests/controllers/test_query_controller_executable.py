from taskdog_core.application.dto.next_tasks_output import RANKING_BASIS
from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.domain.entities.task import Task, TaskStatus


class _Repo:
    def __init__(self, tasks):
        self._tasks = tasks

    def get_filtered(self, **kwargs):
        return list(self._tasks)


class _Time:
    def now(self):
        from datetime import datetime

        return datetime(2026, 7, 18)


def test_get_executable_tasks_returns_ranked_dto():
    tasks = [
        Task(id=1, name="a", priority=1, status=TaskStatus.PENDING),
        Task(id=2, name="b", priority=1, status=TaskStatus.IN_PROGRESS),
    ]
    controller = QueryController(_Repo(tasks), None, _Time())
    out = controller.get_executable_tasks()
    assert [t.id for t in out.tasks] == [2, 1]  # in-progress first
    assert out.ranking_basis == RANKING_BASIS
