"""Help dialog displaying usage instructions and feature guide."""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Markdown, Static

from taskdog import __version__
from taskdog.tui.constants.keybindings import (
    BASIC_WORKFLOW,
    BUG_REPORT_INFO,
    COMMAND_PALETTE_INFO,
    MAIN_FEATURES,
    QUICK_TIPS,
    TASKDOG_OVERVIEW,
)
from taskdog.tui.dialogs.scrollable_dialog import ScrollableDialogBase


class HelpDialog(ScrollableDialogBase[None]):
    """Modal screen displaying help information and usage guide.

    Shows:
    - Basic workflow for new users
    - Main features overview
    - Command palette usage (including Keys command for keybindings)
    - Quick tips
    """

    @property
    def scroll_container_id(self) -> str:
        """Return the ID of the scroll container."""
        return "#help-content"

    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        with Container(
            id="help-screen", classes="dialog-base dialog-wide"
        ) as container:
            container.border_title = f"Taskdog TUI v{__version__} - Getting Started"

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
