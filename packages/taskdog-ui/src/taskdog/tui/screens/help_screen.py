"""Help screen displaying usage instructions and feature guide."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import Markdown, Static

from taskdog.tui.constants.keybindings import (
    BASIC_WORKFLOW,
    BUG_REPORT_INFO,
    COMMAND_PALETTE_INFO,
    MAIN_FEATURES,
    QUICK_TIPS,
    TASKDOG_OVERVIEW,
)
from taskdog.tui.screens.base_dialog import BaseModalDialog
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin


class HelpScreen(BaseModalDialog[None], ViNavigationMixin):
    """Modal screen displaying help information and usage guide.

    Shows:
    - Basic workflow for new users
    - Main features overview
    - Command palette usage (including Keys command for keybindings)
    - Quick tips
    """

    BINDINGS: ClassVar = [
        *ViNavigationMixin.VI_VERTICAL_BINDINGS,
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        Binding("q", "cancel", "Close", tooltip="Close the help screen"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        with Container(
            id="help-screen", classes="dialog-base dialog-wide"
        ) as container:
            container.border_title = "Taskdog TUI - Getting Started"

            with VerticalScroll(id="help-content"):
                # Taskdog Overview
                yield Markdown(TASKDOG_OVERVIEW, classes="help-section")

                # Spacer
                yield Static("", classes="help-spacer")

                # Basic Workflow
                yield Markdown(BASIC_WORKFLOW, classes="help-section")

                # Spacer
                yield Static("", classes="help-spacer")

                # Main Features
                yield Markdown(MAIN_FEATURES, classes="help-section")

                # Spacer
                yield Static("", classes="help-spacer")

                # Command Palette Info (includes Keys command)
                yield Markdown(COMMAND_PALETTE_INFO, classes="help-section")

                # Quick Tips
                yield Static("", classes="help-spacer")
                yield Markdown("## Quick Tips", classes="help-section")
                for tip in QUICK_TIPS:
                    yield Static(tip, classes="help-tip")

                # Bug Reports & Feature Requests
                yield Static("", classes="help-spacer")
                yield Markdown(BUG_REPORT_INFO, classes="help-section")

                # Footer instruction
                yield Static("", classes="help-spacer")
                yield Static(
                    "[dim]Press 'q' or Escape to close • Press Ctrl+P → 'Keys' for all keybindings[/dim]",
                    classes="help-footer",
                )

    def action_vi_down(self) -> None:
        """Scroll down one line (j key)."""
        scroll_widget = self.query_one("#help-content", VerticalScroll)
        scroll_widget.scroll_relative(y=1, animate=False)

    def action_vi_up(self) -> None:
        """Scroll up one line (k key)."""
        scroll_widget = self.query_one("#help-content", VerticalScroll)
        scroll_widget.scroll_relative(y=-1, animate=False)

    def action_vi_page_down(self) -> None:
        """Scroll down half page (Ctrl+D)."""
        scroll_widget = self.query_one("#help-content", VerticalScroll)
        scroll_widget.scroll_relative(y=scroll_widget.size.height // 2, animate=False)

    def action_vi_page_up(self) -> None:
        """Scroll up half page (Ctrl+U)."""
        scroll_widget = self.query_one("#help-content", VerticalScroll)
        scroll_widget.scroll_relative(
            y=-(scroll_widget.size.height // 2), animate=False
        )

    def action_vi_home(self) -> None:
        """Scroll to top (g key)."""
        scroll_widget = self.query_one("#help-content", VerticalScroll)
        scroll_widget.scroll_home(animate=False)

    def action_vi_end(self) -> None:
        """Scroll to bottom (G key)."""
        scroll_widget = self.query_one("#help-content", VerticalScroll)
        scroll_widget.scroll_end(animate=False)
