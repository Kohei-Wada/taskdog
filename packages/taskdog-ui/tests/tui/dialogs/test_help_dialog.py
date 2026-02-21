"""Tests for HelpDialog."""

from unittest.mock import MagicMock

from textual.binding import Binding

from taskdog.tui.dialogs.help_dialog import HelpDialog


class TestHelpDialogClassAttributes:
    """Test cases for HelpDialog class attributes."""

    def test_has_vi_vertical_bindings(self) -> None:
        """Test that VI vertical navigation bindings are included."""
        keys = [b.key for b in HelpDialog.BINDINGS if isinstance(b, Binding)]
        assert "j" in keys
        assert "k" in keys

    def test_has_vi_page_bindings(self) -> None:
        """Test that VI page navigation bindings are included."""
        keys = [b.key for b in HelpDialog.BINDINGS if isinstance(b, Binding)]
        assert "ctrl+d" in keys
        assert "ctrl+u" in keys

    def test_has_cancel_binding(self) -> None:
        """Test that q key is bound to cancel action."""
        q_binding = None
        for binding in HelpDialog.BINDINGS:
            if isinstance(binding, Binding) and binding.key == "q":
                q_binding = binding
                break

        assert q_binding is not None
        assert q_binding.action == "cancel"
        assert "close" in q_binding.description.lower()

    def test_has_tab_switch_bindings(self) -> None:
        """Test that tab switching bindings are included."""
        keys = [b.key for b in HelpDialog.BINDINGS if isinstance(b, Binding)]
        assert "greater_than_sign" in keys
        assert "less_than_sign" in keys


class TestHelpDialogViDownAction:
    """Test cases for action_vi_down method."""

    def test_scrolls_down_one_line(self) -> None:
        """Test that vi_down scrolls content down by 1."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog._get_active_scroll_widget = MagicMock(return_value=mock_scroll)

        dialog.action_vi_down()

        mock_scroll.scroll_relative.assert_called_once_with(y=1, animate=False)

    def test_does_nothing_when_no_active_scroll(self) -> None:
        """Test that vi_down does nothing when no scroll widget is active."""
        dialog = HelpDialog()
        dialog._get_active_scroll_widget = MagicMock(return_value=None)

        dialog.action_vi_down()  # Should not raise


class TestHelpDialogViUpAction:
    """Test cases for action_vi_up method."""

    def test_scrolls_up_one_line(self) -> None:
        """Test that vi_up scrolls content up by 1."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog._get_active_scroll_widget = MagicMock(return_value=mock_scroll)

        dialog.action_vi_up()

        mock_scroll.scroll_relative.assert_called_once_with(y=-1, animate=False)

    def test_does_nothing_when_no_active_scroll(self) -> None:
        """Test that vi_up does nothing when no scroll widget is active."""
        dialog = HelpDialog()
        dialog._get_active_scroll_widget = MagicMock(return_value=None)

        dialog.action_vi_up()  # Should not raise


class TestHelpDialogViPageDownAction:
    """Test cases for action_vi_page_down method."""

    def test_scrolls_down_half_page(self) -> None:
        """Test that vi_page_down scrolls by half the container height."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        mock_scroll.size.height = 20
        dialog._get_active_scroll_widget = MagicMock(return_value=mock_scroll)

        dialog.action_vi_page_down()

        mock_scroll.scroll_relative.assert_called_once_with(y=10, animate=False)

    def test_handles_odd_height(self) -> None:
        """Test that odd height is handled with integer division."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        mock_scroll.size.height = 15  # 15 // 2 = 7
        dialog._get_active_scroll_widget = MagicMock(return_value=mock_scroll)

        dialog.action_vi_page_down()

        mock_scroll.scroll_relative.assert_called_once_with(y=7, animate=False)

    def test_does_nothing_when_no_active_scroll(self) -> None:
        """Test that vi_page_down does nothing when no scroll widget is active."""
        dialog = HelpDialog()
        dialog._get_active_scroll_widget = MagicMock(return_value=None)

        dialog.action_vi_page_down()  # Should not raise


class TestHelpDialogViPageUpAction:
    """Test cases for action_vi_page_up method."""

    def test_scrolls_up_half_page(self) -> None:
        """Test that vi_page_up scrolls up by half the container height."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        mock_scroll.size.height = 20
        dialog._get_active_scroll_widget = MagicMock(return_value=mock_scroll)

        dialog.action_vi_page_up()

        mock_scroll.scroll_relative.assert_called_once_with(y=-10, animate=False)

    def test_does_nothing_when_no_active_scroll(self) -> None:
        """Test that vi_page_up does nothing when no scroll widget is active."""
        dialog = HelpDialog()
        dialog._get_active_scroll_widget = MagicMock(return_value=None)

        dialog.action_vi_page_up()  # Should not raise


class TestHelpDialogViHomeAction:
    """Test cases for action_vi_home method."""

    def test_scrolls_to_top(self) -> None:
        """Test that vi_home scrolls to the top."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog._get_active_scroll_widget = MagicMock(return_value=mock_scroll)

        dialog.action_vi_home()

        mock_scroll.scroll_home.assert_called_once_with(animate=False)

    def test_does_nothing_when_no_active_scroll(self) -> None:
        """Test that vi_home does nothing when no scroll widget is active."""
        dialog = HelpDialog()
        dialog._get_active_scroll_widget = MagicMock(return_value=None)

        dialog.action_vi_home()  # Should not raise


class TestHelpDialogViEndAction:
    """Test cases for action_vi_end method."""

    def test_scrolls_to_bottom(self) -> None:
        """Test that vi_end scrolls to the bottom."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog._get_active_scroll_widget = MagicMock(return_value=mock_scroll)

        dialog.action_vi_end()

        mock_scroll.scroll_end.assert_called_once_with(animate=False)

    def test_does_nothing_when_no_active_scroll(self) -> None:
        """Test that vi_end does nothing when no scroll widget is active."""
        dialog = HelpDialog()
        dialog._get_active_scroll_widget = MagicMock(return_value=None)

        dialog.action_vi_end()  # Should not raise


class TestHelpDialogInheritance:
    """Test cases for HelpDialog inheritance."""

    def test_inherits_from_base_modal_dialog(self) -> None:
        """Test that HelpDialog inherits from BaseModalDialog."""
        from taskdog.tui.dialogs.base_dialog import BaseModalDialog

        assert issubclass(HelpDialog, BaseModalDialog)

    def test_inherits_from_vi_navigation_mixin(self) -> None:
        """Test that HelpDialog inherits from ViNavigationMixin."""
        from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin

        assert issubclass(HelpDialog, ViNavigationMixin)

    def test_does_not_inherit_from_scrollable_dialog_base(self) -> None:
        """Test that HelpDialog no longer inherits from ScrollableDialogBase."""
        from taskdog.tui.dialogs.scrollable_dialog import ScrollableDialogBase

        assert not issubclass(HelpDialog, ScrollableDialogBase)


class TestHelpDialogGetActiveScrollWidget:
    """Test cases for _get_active_scroll_widget method."""

    def test_returns_none_when_tabs_not_found(self) -> None:
        """Test that None is returned when TabbedContent is not found."""
        from textual.css.query import NoMatches

        dialog = HelpDialog()
        dialog.query_one = MagicMock(side_effect=NoMatches())

        result = dialog._get_active_scroll_widget()

        assert result is None

    def test_returns_none_for_unknown_tab(self) -> None:
        """Test that None is returned for an unknown tab pane ID."""
        dialog = HelpDialog()
        mock_tabs = MagicMock()
        mock_tabs.active = "tab-unknown"
        dialog.query_one = MagicMock(return_value=mock_tabs)

        result = dialog._get_active_scroll_widget()

        assert result is None

    def test_returns_scroll_widget_for_active_tab(self) -> None:
        """Test that the correct scroll widget is returned for active tab."""
        from textual.containers import VerticalScroll

        dialog = HelpDialog()
        mock_tabs = MagicMock()
        mock_tabs.active = "tab-getting-started"
        mock_scroll = MagicMock(spec=VerticalScroll)

        def mock_query_one(selector: str, widget_type: type | None = None) -> MagicMock:
            if selector == "#help-tabs":
                return mock_tabs
            if selector == "#help-getting-started-scroll":
                return mock_scroll
            raise Exception(f"Unexpected selector: {selector}")

        dialog.query_one = MagicMock(side_effect=mock_query_one)

        result = dialog._get_active_scroll_widget()

        assert result is mock_scroll

    def test_returns_none_when_scroll_widget_not_found(self) -> None:
        """Test that None is returned when scroll widget raises NoMatches."""
        from textual.css.query import NoMatches

        dialog = HelpDialog()
        mock_tabs = MagicMock()
        mock_tabs.active = "tab-features"

        call_count = 0

        def mock_query_one(selector: str, widget_type: type | None = None) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call: TabbedContent
                return mock_tabs
            raise NoMatches()  # Second call: scroll widget not found

        dialog.query_one = MagicMock(side_effect=mock_query_one)

        result = dialog._get_active_scroll_widget()

        assert result is None


class TestHelpDialogTabSwitchActions:
    """Test cases for tab switching actions."""

    def test_action_next_tab(self) -> None:
        """Test that action_next_tab calls Tabs.action_next_tab."""
        dialog = HelpDialog()
        mock_tabs_widget = MagicMock()
        mock_tabbed_content = MagicMock()
        mock_tabbed_content.query_one.return_value = mock_tabs_widget
        dialog.query_one = MagicMock(return_value=mock_tabbed_content)

        dialog.action_next_tab()

        mock_tabs_widget.action_next_tab.assert_called_once()

    def test_action_prev_tab(self) -> None:
        """Test that action_prev_tab calls Tabs.action_previous_tab."""
        dialog = HelpDialog()
        mock_tabs_widget = MagicMock()
        mock_tabbed_content = MagicMock()
        mock_tabbed_content.query_one.return_value = mock_tabs_widget
        dialog.query_one = MagicMock(return_value=mock_tabbed_content)

        dialog.action_prev_tab()

        mock_tabs_widget.action_previous_tab.assert_called_once()

    def test_action_next_tab_does_nothing_when_no_tabs(self) -> None:
        """Test that action_next_tab does nothing when TabbedContent not found."""
        from textual.css.query import NoMatches

        dialog = HelpDialog()
        dialog.query_one = MagicMock(side_effect=NoMatches())

        dialog.action_next_tab()  # Should not raise

    def test_action_prev_tab_does_nothing_when_no_tabs(self) -> None:
        """Test that action_prev_tab does nothing when TabbedContent not found."""
        from textual.css.query import NoMatches

        dialog = HelpDialog()
        dialog.query_one = MagicMock(side_effect=NoMatches())

        dialog.action_prev_tab()  # Should not raise
