"""Tests for AuditLogTable navigation behavior."""

from unittest.mock import PropertyMock, patch

from taskdog.constants.task_table import PAGE_SCROLL_SIZE
from taskdog.tui.widgets.audit_log_table import AuditLogTable


class TestAuditLogTableCursorType:
    def test_cursor_type_is_row(self) -> None:
        table = AuditLogTable()
        assert table.cursor_type == "row"


class TestAuditLogTableNavActions:
    def test_vi_home_moves_to_first_row(self) -> None:
        table = AuditLogTable()
        calls: list[int] = []
        table.move_cursor = lambda row: calls.append(row)  # type: ignore[assignment]
        with patch.object(
            type(table), "row_count", new_callable=PropertyMock, return_value=10
        ):
            table.action_vi_home()
        assert calls == [0]

    def test_vi_end_moves_to_last_row(self) -> None:
        table = AuditLogTable()
        calls: list[int] = []
        table.move_cursor = lambda row: calls.append(row)  # type: ignore[assignment]
        with patch.object(
            type(table), "row_count", new_callable=PropertyMock, return_value=10
        ):
            table.action_vi_end()
        assert calls == [9]

    def test_vi_page_down_moves_by_page_scroll_size(self) -> None:
        table = AuditLogTable()
        calls: list[int] = []
        table.move_cursor = lambda row: calls.append(row)  # type: ignore[assignment]
        with (
            patch.object(
                type(table), "row_count", new_callable=PropertyMock, return_value=100
            ),
            patch.object(
                type(table), "cursor_row", new_callable=PropertyMock, return_value=5
            ),
        ):
            table.action_vi_page_down()
        assert calls == [5 + PAGE_SCROLL_SIZE]

    def test_vi_page_up_moves_by_page_scroll_size(self) -> None:
        table = AuditLogTable()
        calls: list[int] = []
        table.move_cursor = lambda row: calls.append(row)  # type: ignore[assignment]
        with (
            patch.object(
                type(table), "row_count", new_callable=PropertyMock, return_value=100
            ),
            patch.object(
                type(table), "cursor_row", new_callable=PropertyMock, return_value=20
            ),
        ):
            table.action_vi_page_up()
        assert calls == [20 - PAGE_SCROLL_SIZE]

    def test_vi_page_down_clamps_to_last_row(self) -> None:
        table = AuditLogTable()
        calls: list[int] = []
        table.move_cursor = lambda row: calls.append(row)  # type: ignore[assignment]
        with (
            patch.object(
                type(table), "row_count", new_callable=PropertyMock, return_value=5
            ),
            patch.object(
                type(table), "cursor_row", new_callable=PropertyMock, return_value=3
            ),
        ):
            table.action_vi_page_down()
        assert calls == [4]

    def test_vi_page_up_clamps_to_zero(self) -> None:
        table = AuditLogTable()
        calls: list[int] = []
        table.move_cursor = lambda row: calls.append(row)  # type: ignore[assignment]
        with (
            patch.object(
                type(table), "row_count", new_callable=PropertyMock, return_value=100
            ),
            patch.object(
                type(table), "cursor_row", new_callable=PropertyMock, return_value=2
            ),
        ):
            table.action_vi_page_up()
        assert calls == [0]

    def test_safe_move_cursor_noop_on_empty_table(self) -> None:
        table = AuditLogTable()
        calls: list[int] = []
        table.move_cursor = lambda row: calls.append(row)  # type: ignore[assignment]
        with patch.object(
            type(table), "row_count", new_callable=PropertyMock, return_value=0
        ):
            table._safe_move_cursor(0)
        assert calls == []
