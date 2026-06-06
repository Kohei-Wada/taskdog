"""Tests for GanttDataTable pan key bindings."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from textual.binding import Binding

from taskdog.tui.events import GanttPanRequested
from taskdog.tui.widgets.gantt_data_table import GanttDataTable


def _bindings_by_key() -> dict[str, Binding]:
    return {b.key: b for b in GanttDataTable.BINDINGS if isinstance(b, Binding)}


def _table_with_vm(vm: object | None) -> tuple[GanttDataTable, MagicMock]:
    table = GanttDataTable()  # type: ignore[no-untyped-call]
    table.get_selected_task_vm = MagicMock(return_value=vm)  # type: ignore[method-assign]
    posted = MagicMock()
    table.post_message = posted  # type: ignore[method-assign]
    table.notify = MagicMock()  # type: ignore[method-assign]
    return table, posted


class TestPanBindings:
    """H/L pan the window; lowercase h/l stay cursor movement."""

    def test_capital_h_pans_backward(self) -> None:
        assert _bindings_by_key()["H"].action == "pan_backward"

    def test_capital_l_pans_forward(self) -> None:
        assert _bindings_by_key()["L"].action == "pan_forward"

    def test_lowercase_h_l_remain_cursor_movement(self) -> None:
        keys = _bindings_by_key()
        assert keys["h"].action == "cursor_left"
        assert keys["l"].action == "cursor_right"

    def test_pan_actions_exist(self) -> None:
        assert callable(GanttDataTable.action_pan_backward)
        assert callable(GanttDataTable.action_pan_forward)
        assert callable(GanttDataTable.action_jump_to_today)


class TestJumpToTaskPeriodBinding:
    """Enter jumps the window to the selected task's actual period."""

    def test_enter_jumps_to_task_period(self) -> None:
        assert _bindings_by_key()["enter"].action == "jump_to_task_period"

    def test_action_exists(self) -> None:
        assert callable(GanttDataTable.action_jump_to_task_period)


class TestJumpToTaskPeriodAnchor:
    """Anchor priority: actual_start -> planned_start -> deadline; else no-op."""

    def test_prefers_actual_start(self) -> None:
        vm = SimpleNamespace(
            actual_start=date(2024, 3, 5),
            planned_start=date(2024, 2, 1),
            deadline=date(2024, 4, 1),
        )
        table, posted = _table_with_vm(vm)
        table.action_jump_to_task_period()
        (event,), _ = posted.call_args
        assert isinstance(event, GanttPanRequested)
        assert event.to_date == date(2024, 3, 5)

    def test_falls_back_to_planned_start(self) -> None:
        vm = SimpleNamespace(
            actual_start=None,
            planned_start=date(2024, 2, 1),
            deadline=date(2024, 4, 1),
        )
        table, posted = _table_with_vm(vm)
        table.action_jump_to_task_period()
        (event,), _ = posted.call_args
        assert event.to_date == date(2024, 2, 1)

    def test_falls_back_to_deadline(self) -> None:
        vm = SimpleNamespace(
            actual_start=None,
            planned_start=None,
            deadline=date(2024, 4, 1),
        )
        table, posted = _table_with_vm(vm)
        table.action_jump_to_task_period()
        (event,), _ = posted.call_args
        assert event.to_date == date(2024, 4, 1)

    def test_no_dates_is_noop(self) -> None:
        vm = SimpleNamespace(actual_start=None, planned_start=None, deadline=None)
        table, posted = _table_with_vm(vm)
        table.action_jump_to_task_period()
        posted.assert_not_called()

    def test_no_task_row_is_noop(self) -> None:
        table, posted = _table_with_vm(None)
        table.action_jump_to_task_period()
        posted.assert_not_called()
