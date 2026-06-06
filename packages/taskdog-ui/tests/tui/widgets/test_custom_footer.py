"""Tests for CustomFooter mode-badge formatting."""

from taskdog.tui.widgets.custom_footer import format_mode_badges


class TestFormatModeBadges:
    """format_mode_badges renders the persistent toggle-state badges."""

    def test_sort_always_shown_ascending(self) -> None:
        result = format_mode_badges(
            gantt_filter_enabled=False,
            show_archived=False,
            sort_by="deadline",
            sort_reverse=False,
        )
        assert result == "↑ Deadline"

    def test_sort_descending_arrow(self) -> None:
        result = format_mode_badges(
            gantt_filter_enabled=False,
            show_archived=False,
            sort_by="deadline",
            sort_reverse=True,
        )
        assert result == "↓ Deadline"

    def test_unknown_sort_key_falls_back_to_key(self) -> None:
        result = format_mode_badges(
            gantt_filter_enabled=False,
            show_archived=False,
            sort_by="custom",
            sort_reverse=False,
        )
        assert result == "↑ custom"

    def test_gantt_filter_badge_only_when_enabled(self) -> None:
        result = format_mode_badges(
            gantt_filter_enabled=True,
            show_archived=False,
            sort_by="priority",
            sort_reverse=False,
        )
        assert result == "gantt-filter · ↑ Priority"

    def test_archive_badge_only_when_shown(self) -> None:
        result = format_mode_badges(
            gantt_filter_enabled=False,
            show_archived=True,
            sort_by="priority",
            sort_reverse=False,
        )
        assert result == "archived · ↑ Priority"

    def test_both_toggles_ordered_filter_then_archive_then_sort(self) -> None:
        result = format_mode_badges(
            gantt_filter_enabled=True,
            show_archived=True,
            sort_by="id",
            sort_reverse=True,
        )
        assert result == "gantt-filter · archived · ↓ ID"

    def test_no_square_brackets_to_avoid_markup_collision(self) -> None:
        result = format_mode_badges(
            gantt_filter_enabled=True,
            show_archived=True,
            sort_by="deadline",
            sort_reverse=False,
        )
        assert "[" not in result
        assert "]" not in result
