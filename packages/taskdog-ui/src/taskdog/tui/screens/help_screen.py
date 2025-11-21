"""Help screen displaying keybindings and usage instructions."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import Label, Static

from taskdog.tui.constants.keybindings import (
    CATEGORY_ORDER,
    COMMAND_PALETTE_INFO,
    KEYBINDINGS_BY_CATEGORY,
    QUICK_START_TIPS,
    SEARCH_USAGE_INFO,
    KeyBinding,
)
from taskdog.tui.screens.base_dialog import BaseModalDialog
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin


class HelpScreen(BaseModalDialog[None], ViNavigationMixin):
    """Modal screen displaying help information and keybindings.

    Shows:
    - Categorized keybindings (Navigation, Task Operations, etc.)
    - Quick start tips for new users
    - Command palette usage instructions
    - Search feature explanation
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
            container.border_title = "Taskdog TUI - Help & Keybindings"

            with VerticalScroll(id="help-content"):
                # Title
                yield Label(
                    "[bold cyan]Keyboard Shortcuts[/bold cyan]",
                    classes="help-section-title",
                )

                # Keybindings by category
                for category_name in CATEGORY_ORDER:
                    if category_name not in KEYBINDINGS_BY_CATEGORY:
                        continue

                    bindings = KEYBINDINGS_BY_CATEGORY[category_name]
                    yield from self._compose_category_section(category_name, bindings)

                # Quick Start Tips
                yield Static("", classes="help-spacer")
                yield Label(
                    "[bold cyan]Quick Start Tips[/bold cyan]",
                    classes="help-section-title",
                )
                for tip in QUICK_START_TIPS:
                    yield Static(f"• {tip}", classes="help-tip")

                # Command Palette Info
                yield Static("", classes="help-spacer")
                yield Label(
                    "[bold cyan]Command Palette[/bold cyan]",
                    classes="help-section-title",
                )
                yield Static(COMMAND_PALETTE_INFO, classes="help-info-block")

                # Search Usage Info
                yield Static("", classes="help-spacer")
                yield Label(
                    "[bold cyan]Search Feature[/bold cyan]",
                    classes="help-section-title",
                )
                yield Static(SEARCH_USAGE_INFO, classes="help-info-block")

                # Footer instruction
                yield Static("", classes="help-spacer")
                yield Static(
                    "[dim]Press 'q' or Escape to close this help screen[/dim]",
                    classes="help-footer",
                )

    def _compose_category_section(
        self, category_name: str, bindings: list[KeyBinding]
    ) -> ComposeResult:
        """Compose a category section with its keybindings.

        Args:
            category_name: Name of the category (e.g., "Navigation")
            bindings: List of keybinding dictionaries

        Yields:
            Widgets for the category section
        """
        # Category header
        yield Static("", classes="help-spacer-small")
        yield Label(
            f"[bold yellow]{category_name}[/bold yellow]", classes="help-category"
        )

        # Keybindings table
        for binding in bindings:
            key = binding["key"]
            action = binding["action"]
            description = binding["description"]

            # Format: "Key        Action               Description"
            # Use fixed-width formatting for alignment
            key_part = f"[cyan]{key:20s}[/cyan]"
            action_part = f"[white]{action:20s}[/white]"
            desc_part = f"[dim]{description}[/dim]"

            yield Static(
                f"{key_part} {action_part} {desc_part}",
                classes="help-binding-row",
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
