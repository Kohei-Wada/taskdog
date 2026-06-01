"""Tests for AuditLogTable keyboard navigation behavior."""

from taskdog.tui.widgets.audit_log_table import AuditLogTable


class TestAuditLogTablePageScrollActions:
    """Ctrl+d/Ctrl+u should use discrete page scrolling like other audit log moves."""

    def test_page_down_disables_animation(self, monkeypatch) -> None:
        calls: list[bool] = []
        table = AuditLogTable()

        monkeypatch.setattr(
            table, "scroll_page_down", lambda *, animate: calls.append(animate)
        )

        table.action_page_down()

        assert calls == [False]

    def test_page_up_disables_animation(self, monkeypatch) -> None:
        calls: list[bool] = []
        table = AuditLogTable()

        monkeypatch.setattr(
            table, "scroll_page_up", lambda *, animate: calls.append(animate)
        )

        table.action_page_up()

        assert calls == [False]
