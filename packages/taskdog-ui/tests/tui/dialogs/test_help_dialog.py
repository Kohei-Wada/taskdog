"""Tests for HelpDialog."""

from unittest.mock import MagicMock

from textual.binding import Binding

from taskdog.tui.dialogs.help_dialog import HelpDialog


class TestHelpDialogClassAttributes:
    """Test cases for HelpDialog class attributes."""

    def test_has_vi_vertical_bindings(self) -> None:
        """Test that VI vertical navigation bindings are included."""
        # Check that j/k bindings are present
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


class TestHelpDialogViDownAction:
    """Test cases for action_vi_down method."""

    def test_scrolls_down_one_line(self) -> None:
        """Test that vi_down scrolls content down by 1."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog.query_one = MagicMock(return_value=mock_scroll)

        dialog.action_vi_down()

        mock_scroll.scroll_relative.assert_called_once_with(y=1, animate=False)

    def test_queries_correct_widget(self) -> None:
        """Test that action queries the correct widget."""
        from textual.containers import VerticalScroll

        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog.query_one = MagicMock(return_value=mock_scroll)

        dialog.action_vi_down()

        dialog.query_one.assert_called_once_with("#help-content", VerticalScroll)


class TestHelpDialogViUpAction:
    """Test cases for action_vi_up method."""

    def test_scrolls_up_one_line(self) -> None:
        """Test that vi_up scrolls content up by 1."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog.query_one = MagicMock(return_value=mock_scroll)

        dialog.action_vi_up()

        mock_scroll.scroll_relative.assert_called_once_with(y=-1, animate=False)


class TestHelpDialogViPageDownAction:
    """Test cases for action_vi_page_down method."""

    def test_scrolls_down_half_page(self) -> None:
        """Test that vi_page_down scrolls by half the container height."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        mock_scroll.size.height = 20  # Simulate 20 rows height
        dialog.query_one = MagicMock(return_value=mock_scroll)

        dialog.action_vi_page_down()

        mock_scroll.scroll_relative.assert_called_once_with(y=10, animate=False)

    def test_handles_odd_height(self) -> None:
        """Test that odd height is handled with integer division."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        mock_scroll.size.height = 15  # 15 // 2 = 7
        dialog.query_one = MagicMock(return_value=mock_scroll)

        dialog.action_vi_page_down()

        mock_scroll.scroll_relative.assert_called_once_with(y=7, animate=False)


class TestHelpDialogViPageUpAction:
    """Test cases for action_vi_page_up method."""

    def test_scrolls_up_half_page(self) -> None:
        """Test that vi_page_up scrolls up by half the container height."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        mock_scroll.size.height = 20
        dialog.query_one = MagicMock(return_value=mock_scroll)

        dialog.action_vi_page_up()

        mock_scroll.scroll_relative.assert_called_once_with(y=-10, animate=False)


class TestHelpDialogViHomeAction:
    """Test cases for action_vi_home method."""

    def test_scrolls_to_top(self) -> None:
        """Test that vi_home scrolls to the top."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog.query_one = MagicMock(return_value=mock_scroll)

        dialog.action_vi_home()

        mock_scroll.scroll_home.assert_called_once_with(animate=False)


class TestHelpDialogViEndAction:
    """Test cases for action_vi_end method."""

    def test_scrolls_to_bottom(self) -> None:
        """Test that vi_end scrolls to the bottom."""
        dialog = HelpDialog()
        mock_scroll = MagicMock()
        dialog.query_one = MagicMock(return_value=mock_scroll)

        dialog.action_vi_end()

        mock_scroll.scroll_end.assert_called_once_with(animate=False)


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
