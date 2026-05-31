"""Startup smoke test for the TUI.

Verifies that the initial task load is offloaded to a background worker so it
does not block first paint: even when the (synchronous) API client is slow,
mounting the app must complete promptly, and the task list fills in afterwards.
"""

import asyncio
from datetime import datetime
from threading import Event

import pytest

from taskdog.tui.app import TaskdogTUI
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus


def _make_task(task_id: int) -> TaskRowDto:
    return TaskRowDto(
        id=task_id,
        name=f"Task {task_id}",
        status=TaskStatus.PENDING,
        priority=1,
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
        is_archived=False,
        is_finished=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class _BlockingApiClient:
    """Synchronous API client whose list_tasks blocks until released.

    Simulates a slow/unreachable server. If the initial load ran on the event
    loop, mounting would block here; with the worker offload it does not.
    """

    def __init__(self) -> None:
        self.base_url = "http://test"
        self.api_key = None
        self.release = Event()
        self.list_calls = 0

    def list_tasks(self, **kwargs: object) -> TaskListOutput:
        self.list_calls += 1
        # Block the worker thread until the test releases it.
        self.release.wait(timeout=5)
        return TaskListOutput(
            tasks=[_make_task(1), _make_task(2)],
            total_count=2,
            filtered_count=2,
            gantt_data=None,
        )

    def check_health(self) -> bool:
        return True


class _FakeWebSocketClient:
    """Minimal stand-in for WebSocketClient (no real network)."""

    def __init__(self) -> None:
        self._callback = None

    def set_callback(self, on_message: object) -> None:
        self._callback = on_message

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    def is_connected(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_initial_load_does_not_block_first_paint() -> None:
    """Mount completes while the slow fetch is still in flight; data fills in after."""
    api = _BlockingApiClient()
    app = TaskdogTUI(api_client=api, websocket_client=_FakeWebSocketClient())

    async with app.run_test() as pilot:
        # Reaching here at all proves on_mount did not block on list_tasks.
        # Wait until the worker thread has entered the (blocked) fetch.
        for _ in range(200):
            if api.list_calls >= 1:
                break
            await asyncio.sleep(0.01)
        assert api.list_calls >= 1, "initial load was never dispatched to a worker"

        # The fetch is still blocked, so no rows are cached yet — the UI is not
        # frozen waiting for it.
        assert app.state.viewmodels_cache == []

        # Release the fetch and let the worker apply the result on the main thread.
        api.release.set()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert len(app.state.viewmodels_cache) == 2
