"""Tests for audit_log_formatter (Rich-free helpers)."""

from taskdog.formatters.audit_log_formatter import compact_changes, truncate_error
from taskdog.view_models.audit_log_view_model import AuditChangeViewModel


def _c(key, old, new):
    return AuditChangeViewModel(key=key, old=old, new=new)


class TestCompactChanges:
    def test_empty_returns_empty_string(self):
        assert compact_changes((), max_length=40) == ""

    def test_single_change(self):
        assert compact_changes((_c("priority", "3", "5"),), max_length=40) == (
            "priority: 3 → 5"
        )

    def test_two_changes_joined(self):
        result = compact_changes((_c("a", "1", "2"), _c("b", "3", "4")), max_length=40)
        assert result == "a: 1 → 2, b: 3 → 4"

    def test_more_than_two_changes_are_capped(self):
        result = compact_changes(
            (_c("a", "1", "2"), _c("b", "3", "4"), _c("c", "5", "6")),
            max_length=40,
        )
        assert result == "a: 1 → 2, b: 3 → 4 (+1)"

    def test_truncates_to_max_length(self):
        result = compact_changes(
            (_c("description", "old value here", "new value here"),),
            max_length=10,
        )
        assert result == "descrip..."
        assert len(result) == 10


class TestTruncateError:
    def test_short_message_unchanged(self):
        assert truncate_error("boom", max_length=40) == "boom"

    def test_long_message_truncated_with_ellipsis(self):
        msg = "x" * 50
        assert truncate_error(msg, max_length=40) == "x" * 40 + "..."
