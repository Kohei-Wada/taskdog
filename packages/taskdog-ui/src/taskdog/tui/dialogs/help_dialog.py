"""Help dialog displaying usage instructions and feature guide."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Markdown, Static, TabbedContent, TabPane, Tabs

from taskdog import __version__
from taskdog.tui.constants.keybindings import (
    BASIC_WORKFLOW,
    BUG_REPORT_INFO,
    COMMAND_PALETTE_INFO,
    MAIN_FEATURES,
    QUICK_TIPS,
    TASKDOG_OVERVIEW,
)
from taskdog.tui.dialogs.base_dialog import BaseModalDialog
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin

# Mapping from tab pane ID to its VerticalScroll child ID
_TAB_SCROLL_MAP: dict[str, str] = {
    "tab-getting-started": "help-getting-started-scroll",
    "tab-features": "help-features-scroll",
    "tab-tips": "help-tips-scroll",
}


class HelpDialog(BaseModalDialog[None], ViNavigationMixin):
    """Modal screen displaying help information and usage guide.

    Organized into three tabs:
    - Getting Started: Overview and basic workflow
    - Features: Main features and command palette
    - Tips: Quick tips and bug report info
    """

    BINDINGS: ClassVar = [
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        Binding("q", "cancel", "Close", tooltip="Close the dialog"),
        Binding("greater_than_sign", "next_tab", "Next Tab", show=False, priority=True),
        Binding("less_than_sign", "prev_tab", "Prev Tab", show=False, priority=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        with Container(
            id="help-screen", classes="dialog-base dialog-wide"
        ) as container:
            container.border_title = f"Taskdog TUI v{__version__} - Getting Started"

            with TabbedContent(id="help-tabs"):
                # Tab 1: Getting Started
                with (
                    TabPane("Getting Started", id="tab-getting-started"),
                    VerticalScroll(
                        id="help-getting-started-scroll",
                        classes="help-tab-scroll",
                    ),
                ):
                    yield Markdown(TASKDOG_OVERVIEW, classes="help-section")
                    yield Static("", classes="help-spacer")
                    yield Markdown(BASIC_WORKFLOW, classes="help-section")

                # Tab 2: Features
                with (
                    TabPane("Features", id="tab-features"),
                    VerticalScroll(
                        id="help-features-scroll",
                        classes="help-tab-scroll",
                    ),
                ):
                    yield Markdown(MAIN_FEATURES, classes="help-section")
                    yield Static("", classes="help-spacer")
                    yield Markdown(COMMAND_PALETTE_INFO, classes="help-section")

                # Tab 3: Tips
                with (
                    TabPane("Tips", id="tab-tips"),
                    VerticalScroll(
                        id="help-tips-scroll",
                        classes="help-tab-scroll",
                    ),
                ):
                    yield Markdown("## Quick Tips", classes="help-section")
                    for tip in QUICK_TIPS:
                        yield Static(tip, classes="help-tip")
                    yield Static("", classes="help-spacer")
                    yield Markdown(BUG_REPORT_INFO, classes="help-section")

            # Footer instruction
            yield Static(
                "[dim]Press 'q' or Escape to close • '<' / '>' to switch tabs • Press Ctrl+P → 'Keys' for all keybindings[/dim]",
                classes="help-footer",
            )

    def _get_active_scroll_widget(self) -> VerticalScroll | None:
        """Get the VerticalScroll widget for the currently active tab.

        Returns:
            The active tab's VerticalScroll widget, or None if not found.
        """
        try:
            tabs = self.query_one("#help-tabs", TabbedContent)
        except NoMatches:
            return None

        active_pane = tabs.active
        scroll_id = _TAB_SCROLL_MAP.get(active_pane, "")
        if not scroll_id:
            return None

        try:
            return self.query_one(f"#{scroll_id}", VerticalScroll)
        except NoMatches:
            return None

    def action_vi_down(self) -> None:
        """Scroll down one line (j key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=1, animate=False)

    def action_vi_up(self) -> None:
        """Scroll up one line (k key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=-1, animate=False)

    def action_vi_page_down(self) -> None:
        """Scroll down half page (Ctrl+D)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=widget.size.height // 2, animate=False)

    def action_vi_page_up(self) -> None:
        """Scroll up half page (Ctrl+U)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_relative(y=-(widget.size.height // 2), animate=False)

    def action_vi_home(self) -> None:
        """Scroll to top (g key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_home(animate=False)

    def action_vi_end(self) -> None:
        """Scroll to bottom (G key)."""
        widget = self._get_active_scroll_widget()
        if widget:
            widget.scroll_end(animate=False)

    def action_next_tab(self) -> None:
        """Switch to the next tab (> key)."""
        try:
            tabs = self.query_one("#help-tabs", TabbedContent).query_one(Tabs)
            tabs.action_next_tab()
        except NoMatches:
            pass

    def action_prev_tab(self) -> None:
        """Switch to the previous tab (< key)."""
        try:
            tabs = self.query_one("#help-tabs", TabbedContent).query_one(Tabs)
            tabs.action_previous_tab()
        except NoMatches:
            pass
