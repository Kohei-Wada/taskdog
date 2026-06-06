"""Tests for GanttWidget time-window panning."""

from datetime import date, timedelta
from unittest.mock import MagicMock

from taskdog.tui.events import GanttPanRequested
from taskdog.tui.widgets.gantt_widget import GanttWidget
from taskdog_core.shared.constants.time import DAYS_PER_WEEK


def _this_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


class TestPanOffsetMath:
    """The window start shifts by the pan offset while width stays fixed."""

    def test_zero_offset_starts_this_monday(self) -> None:
        widget = GanttWidget()
        start, end = widget._calculate_date_range_for_display(7)
        assert start == _this_monday()
        assert (end - start).days + 1 == 7

    def test_negative_offset_shifts_into_past(self) -> None:
        widget = GanttWidget()
        widget._pan_offset_days = -2 * DAYS_PER_WEEK
        start, end = widget._calculate_date_range_for_display(7)
        assert start == _this_monday() - timedelta(days=14)
        assert (end - start).days + 1 == 7  # width unchanged


class TestPanHandler:
    """on_gantt_pan_requested updates the offset and triggers a refetch."""

    def _widget(self) -> GanttWidget:
        widget = GanttWidget()
        widget._calculate_display_days = MagicMock(return_value=7)  # type: ignore[method-assign]
        widget._recalculate_gantt_for_width = MagicMock()  # type: ignore[method-assign]
        return widget

    def test_pan_backward_accumulates(self) -> None:
        widget = self._widget()
        widget.on_gantt_pan_requested(GanttPanRequested(weeks=-1))
        widget.on_gantt_pan_requested(GanttPanRequested(weeks=-1))
        assert widget._pan_offset_days == -2 * DAYS_PER_WEEK
        assert widget._recalculate_gantt_for_width.call_count == 2

    def test_pan_forward_then_back_nets_out(self) -> None:
        widget = self._widget()
        widget.on_gantt_pan_requested(GanttPanRequested(weeks=3))
        widget.on_gantt_pan_requested(GanttPanRequested(weeks=-3))
        assert widget._pan_offset_days == 0

    def test_reset_snaps_to_today(self) -> None:
        widget = self._widget()
        widget._pan_offset_days = -5 * DAYS_PER_WEEK
        widget.on_gantt_pan_requested(GanttPanRequested(reset=True))
        assert widget._pan_offset_days == 0
        widget._recalculate_gantt_for_width.assert_called_once()

    def test_reset_when_already_today_is_noop(self) -> None:
        widget = self._widget()
        widget.on_gantt_pan_requested(GanttPanRequested(reset=True))
        assert widget._pan_offset_days == 0
        widget._recalculate_gantt_for_width.assert_not_called()

    def test_jump_to_date_sets_offset_to_that_week(self) -> None:
        widget = self._widget()
        target = _this_monday() + timedelta(days=3 * DAYS_PER_WEEK + 2)  # mid-week
        widget.on_gantt_pan_requested(GanttPanRequested(to_date=target))
        # Window start lands on the Monday of the target's week.
        assert widget._pan_offset_days == 3 * DAYS_PER_WEEK
        start, _ = widget._calculate_date_range_for_display(7)
        assert start == _this_monday() + timedelta(days=3 * DAYS_PER_WEEK)
        widget._recalculate_gantt_for_width.assert_called_once()

    def test_jump_to_past_date_sets_negative_offset(self) -> None:
        widget = self._widget()
        target = _this_monday() - timedelta(days=10)
        widget.on_gantt_pan_requested(GanttPanRequested(to_date=target))
        target_monday = target - timedelta(days=target.weekday())
        assert widget._pan_offset_days == (target_monday - _this_monday()).days
