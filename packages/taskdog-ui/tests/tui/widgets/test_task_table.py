"""Tests for TaskTable keyboard navigation bindings."""

from textual.binding import Binding

from taskdog.constants.task_table import (
    HORIZONTAL_FAST_SCROLL_SIZE,
    HORIZONTAL_SCROLL_SIZE,
)
from taskdog.tui.widgets.task_table import TaskTable


def _bindings_by_key() -> dict[str, Binding]:
    return {b.key: b for b in TaskTable.BINDINGS if isinstance(b, Binding)}


class TestTaskTableFastScrollBindings:
    """w/b provide fast horizontal scrolling, mirroring the gantt week-jump."""

    def test_w_bound_to_fast_right_scroll(self) -> None:
        assert _bindings_by_key()["w"].action == "vi_scroll_right_fast"

    def test_b_bound_to_fast_left_scroll(self) -> None:
        assert _bindings_by_key()["b"].action == "vi_scroll_left_fast"

    def test_fast_scroll_actions_exist(self) -> None:
        assert callable(TaskTable.action_vi_scroll_right_fast)
        assert callable(TaskTable.action_vi_scroll_left_fast)

    def test_fast_step_is_larger_than_normal_step(self) -> None:
        assert HORIZONTAL_FAST_SCROLL_SIZE > HORIZONTAL_SCROLL_SIZE
