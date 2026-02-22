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
    "tab-keybindings": "help-keybindings-scroll",
}

# Category display order for the auto-generated Keybindings tab
_CATEGORY_ORDER: list[str] = [
    "Task Actions",
    "Task Management",
    "Selection",
    "Navigation",
    "View & Search",
    "General",
]

# Action name → Category mapping for keybindings auto-generation
_ACTION_CATEGORIES: dict[str, str] = {
    # Task Actions
    "add": "Task Actions",
    "start": "Task Actions",
    "done": "Task Actions",
    "pause": "Task Actions",
    "cancel": "Task Actions",
    "reopen": "Task Actions",
    # Task Management
    "edit": "Task Management",
    "fix_actual": "Task Management",
    "show": "Task Management",
    "note": "Task Management",
    "rm": "Task Management",
    "hard_delete": "Task Management",
    # Selection
    "toggle_selection": "Selection",
    "select_all": "Selection",
    "clear_selection": "Selection",
    # Navigation
    "cursor_down": "Navigation",
    "cursor_up": "Navigation",
    "vi_home": "Navigation",
    "vi_end": "Navigation",
    "vi_page_down": "Navigation",
    "vi_page_up": "Navigation",
    "vi_scroll_left": "Navigation",
    "vi_scroll_right": "Navigation",
    "vi_home_horizontal": "Navigation",
    "vi_end_horizontal": "Navigation",
    "focus_next": "Navigation",
    "focus_previous": "Navigation",
    # View & Search
    "show_search": "View & Search",
    "hide_search": "View & Search",
    "toggle_sort_reverse": "View & Search",
    "toggle_maximize": "View & Search",
    "toggle_gantt_filter": "View & Search",
    "stats": "View & Search",
    "refresh": "View & Search",
    # General
    "quit": "General",
    "show_help": "General",
    "command_palette": "General",
}

# Special key name → display name mapping
_KEY_DISPLAY_MAP: dict[str, str] = {
    "greater_than_sign": ">",
    "less_than_sign": "<",
    "space": "Space",
    "escape": "Escape",
}


def _format_key_display(key: str) -> str:
    """Format a binding key string for user-friendly display.

    Args:
        key: Raw key string from Binding definition.

    Returns:
        Formatted key string for display.
    """
    if key in _KEY_DISPLAY_MAP:
        return _KEY_DISPLAY_MAP[key]
    if key.startswith("ctrl+"):
        return "Ctrl+" + key[5:].upper()
    return key


class HelpDialog(BaseModalDialog[None], ViNavigationMixin):
    """Modal screen displaying help information and usage guide.

    Organized into four tabs:
    - Getting Started: Overview and basic workflow
    - Features: Main features and command palette
    - Tips: Quick tips and bug report info
    - Keybindings: Auto-generated keybinding reference from Binding definitions
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

                # Tab 4: Keybindings (auto-generated from Binding definitions)
                with (
                    TabPane("Keybindings", id="tab-keybindings"),
                    VerticalScroll(
                        id="help-keybindings-scroll",
                        classes="help-tab-scroll",
                    ),
                ):
                    yield Markdown(
                        self._build_keybindings_content(),
                        classes="help-section",
                    )

            # Footer instruction
            yield Static(
                "[dim]Press 'q' or Escape to close • '<' / '>' to switch tabs[/dim]",
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

    def _build_keybindings_content(self) -> str:
        """Build keybindings reference from actual Binding definitions.

        Collects bindings from TaskdogTUI, MainScreen, and TaskTable,
        groups them by category, and generates a Markdown table.

        Returns:
            Markdown string with categorized keybinding tables.
        """
        from taskdog.tui.screens.main_screen import MainScreen
        from taskdog.tui.widgets.task_table import TaskTable

        # Collect bindings from all sources
        all_bindings: list[Binding] = []
        all_bindings.extend(type(self.app).BINDINGS)  # type: ignore[arg-type]
        all_bindings.extend(MainScreen.BINDINGS)  # type: ignore[arg-type]
        all_bindings.extend(TaskTable.BINDINGS)  # type: ignore[arg-type]

        # Group by category, deduplicating by (key, action) pair
        seen: set[tuple[str, str]] = set()
        categories: dict[str, list[tuple[str, str]]] = {
            cat: [] for cat in _CATEGORY_ORDER
        }

        for binding in all_bindings:
            if not isinstance(binding, Binding):
                continue
            action = binding.action
            key = binding.key
            if (key, action) in seen:
                continue
            seen.add((key, action))

            category = _ACTION_CATEGORIES.get(action)
            if category is None:
                continue

            display_key = _format_key_display(key)
            tooltip = binding.tooltip or binding.description
            categories[category].append((display_key, tooltip))

        # Add command palette entry (configured via Textual's COMMAND_PALETTE_BINDING)
        categories["General"].append(("Ctrl+P", "Open command palette"))

        # Build Markdown content
        lines: list[str] = ["## Keybindings Reference\n"]
        for category in _CATEGORY_ORDER:
            items = categories.get(category, [])
            if not items:
                continue
            lines.append(f"### {category}\n")
            lines.append("| Key | Description |")
            lines.append("|-----|-------------|")
            for key_display, desc in items:
                lines.append(f"| `{key_display}` | {desc} |")
            lines.append("")

        return "\n".join(lines)

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
