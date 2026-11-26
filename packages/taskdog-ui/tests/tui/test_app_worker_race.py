"""Regression tests for concurrent reload and gantt worker races in TaskdogTUI."""

import threading
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from taskdog.tui.app import TaskdogTUI
from taskdog.tui.events import GanttResizeRequested
from taskdog_core.application.dto.gantt_overlay import GanttDateRange, GanttOverlay
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus


def _make_task_dto(task_id: int, name: str) -> TaskRowDto:
    now = datetime.now()
    return TaskRowDto(
        id=task_id,
        name=name,
        status=TaskStatus.PENDING,
        priority=1,
        planned_start=None,
        planned_end=None,
        deadline=None,
        actual_start=None,
        actual_end=None,
        estimated_duration=1.0,
        actual_duration_hours=None,
        is_fixed=False,
        depends_on=[],
        tags=[],
        is_archived=False,
        is_finished=False,
        created_at=now,
        updated_at=now,
    )


def _make_task_list_output(
    tasks: list[TaskRowDto], start_date: date, end_date: date
) -> TaskListOutput:
    return TaskListOutput(
        tasks=tasks,
        total_count=len(tasks),
        filtered_count=len(tasks),
        gantt_data=GanttOverlay(
            date_range=GanttDateRange(start_date=start_date, end_date=end_date),
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
        ),
    )


def _make_app(list_tasks_impl: Any) -> TaskdogTUI:
    api_client = MagicMock()
    api_client.client_id = "test"
    api_client.list_tasks.side_effect = list_tasks_impl
    api_client.check_health.return_value = True
    ws = MagicMock()
    ws.connect = AsyncMock()
    ws.disconnect = AsyncMock()
    ws.is_connected.return_value = True
    return TaskdogTUI(api_client=api_client, websocket_client=ws)


async def _wait_until(
    pilot: Any, predicate: Callable[[], bool], *, step: float = 0.02
) -> None:
    for _ in range(30):
        await pilot.pause(step)
        if predicate():
            return
    assert predicate()


async def _wait_group(app: TaskdogTUI, pilot: Any, group: str) -> None:
    for worker in [w for w in app.workers if w.group == group]:
        await worker.wait()
    await pilot.pause(0.02)


class TestWorkerCacheRace:
    @pytest.mark.asyncio
    async def test_slow_stale_gantt_fetch_does_not_overwrite_newer_reload(
        self,
    ) -> None:
        """Slow gantt pan/resize fetch started before a reload must be dropped."""
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())
        old_start = this_monday + timedelta(days=7)
        old_end = old_start + timedelta(days=6)
        new_start = this_monday + timedelta(days=14)
        new_end = new_start + timedelta(days=6)

        gantt_entered = threading.Event()
        gantt_release = threading.Event()
        reload_done = threading.Event()
        call_count = 0

        def _list_tasks(**kwargs: Any) -> TaskListOutput:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_task_list_output(
                    [_make_task_dto(1, "Initial Task")],
                    kwargs["gantt_start_date"],
                    kwargs["gantt_end_date"],
                )
            if kwargs.get("gantt_start_date") == old_start:
                gantt_entered.set()
                gantt_release.wait(timeout=5)
                return _make_task_list_output(
                    [_make_task_dto(1, "Stale Task")],
                    old_start,
                    old_end,
                )
            output = _make_task_list_output(
                [_make_task_dto(1, "Initial Task"), _make_task_dto(2, "Fresh Task")],
                new_start,
                new_end,
            )
            reload_done.set()
            return output

        app = _make_app(_list_tasks)
        async with app.run_test(size=(120, 40)) as pilot:
            await _wait_until(
                pilot, lambda: app.state.gantt_cache is not None, step=0.05
            )
            assert app.main_screen is not None
            assert app.main_screen.gantt_widget is not None
            app.main_screen.gantt_widget._recalculate_gantt_for_width = MagicMock()  # type: ignore[method-assign]

            app.post_message(GanttResizeRequested(7, old_start, old_end))
            await _wait_until(pilot, gantt_entered.is_set)

            app.main_screen.gantt_widget.calculate_date_range = MagicMock(
                return_value=(new_start, new_end)
            )
            app._flush_reload()
            await _wait_until(pilot, reload_done.is_set)
            await pilot.pause(0.05)

            assert app.state.gantt_cache is not None
            assert [t.id for t in app.state.gantt_cache.tasks] == [1, 2]
            assert app.state.gantt_cache.start_date == new_start

            gantt_release.set()
            await _wait_group(app, pilot, "gantt")

            assert [t.id for t in app.state.gantt_cache.tasks] == [1, 2]
            assert app.state.gantt_cache.start_date == new_start

    @pytest.mark.asyncio
    async def test_slow_reload_does_not_overwrite_newer_gantt_cache(self) -> None:
        """Slow reload started before a gantt pan keeps table fresh without clobbering gantt."""
        today = date.today()
        old_start = today
        old_end = today + timedelta(days=6)
        new_start = today + timedelta(days=14)
        new_end = today + timedelta(days=20)

        reload_entered = threading.Event()
        reload_release = threading.Event()
        gantt_done = threading.Event()
        call_count = 0

        def _list_tasks(**kwargs: Any) -> TaskListOutput:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_task_list_output(
                    [_make_task_dto(1, "Initial Task")],
                    kwargs["gantt_start_date"],
                    kwargs["gantt_end_date"],
                )
            if kwargs.get("gantt_start_date") == old_start:
                reload_entered.set()
                reload_release.wait(timeout=5)
                return _make_task_list_output(
                    [_make_task_dto(1, "Initial Task"), _make_task_dto(2, "Reloaded")],
                    old_start,
                    old_end,
                )
            output = _make_task_list_output(
                [_make_task_dto(1, "Initial Task"), _make_task_dto(2, "Reloaded")],
                new_start,
                new_end,
            )
            gantt_done.set()
            return output

        app = _make_app(_list_tasks)
        async with app.run_test(size=(120, 40)) as pilot:
            await _wait_until(
                pilot, lambda: app.state.gantt_cache is not None, step=0.05
            )
            assert app.main_screen is not None
            assert app.main_screen.gantt_widget is not None
            app.main_screen.gantt_widget._recalculate_gantt_for_width = MagicMock()  # type: ignore[method-assign]
            app.main_screen.gantt_widget.calculate_date_range = MagicMock(
                return_value=(old_start, old_end)
            )

            app._flush_reload()
            await _wait_until(pilot, reload_entered.is_set)

            app.post_message(GanttResizeRequested(7, new_start, new_end))
            await _wait_until(pilot, gantt_done.is_set)
            await pilot.pause(0.05)

            assert app.state.gantt_cache is not None
            assert app.state.gantt_cache.start_date == new_start

            reload_release.set()
            await _wait_group(app, pilot, "reload")

            assert [vm.id for vm in app.state.viewmodels_cache] == [1, 2]
            assert app.state.gantt_cache.start_date == new_start
