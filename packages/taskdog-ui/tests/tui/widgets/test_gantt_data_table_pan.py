"""Tests for GanttDataTable pan key bindings."""

from textual.binding import Binding

from taskdog.tui.widgets.gantt_data_table import GanttDataTable


def _bindings_by_key() -> dict[str, Binding]:
    return {b.key: b for b in GanttDataTable.BINDINGS if isinstance(b, Binding)}


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
