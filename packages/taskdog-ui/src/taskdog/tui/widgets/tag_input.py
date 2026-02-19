"""Tag input widget with suggestion dropdown."""

from __future__ import annotations

import re

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.events import Key
from textual.message import Message
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option


class _NonFocusableOptionList(OptionList):
    """OptionList subclass that cannot receive focus.

    This prevents Tab/Shift+Tab from stopping on the dropdown,
    keeping normal form navigation intact.
    """

    can_focus = False


# Regex for validating tag input (allows trailing comma for mid-input state)
_TAG_PATTERN = re.compile(r"^([a-zA-Z0-9_-]+\s*,\s*)*[a-zA-Z0-9_-]*$")


class TagInput(Vertical):
    """Composite widget for tag input with suggestion dropdown.

    Combines an Input field with an OptionList dropdown that shows
    matching tag suggestions as the user types. Tags are comma-separated.
    The dropdown only appears when the input field has focus.

    Attributes:
        value: Current text value of the input field.
        is_valid: Whether the current input passes validation.
    """

    DEFAULT_CSS = """
    TagInput {
        height: auto;
    }
    TagInput ._non-focusable-option-list {
        display: none;
        max-height: 6;
        border: round $accent;
        background: $surface;
        margin: 0;
        padding: 0;
    }
    TagInput ._non-focusable-option-list.visible {
        display: block;
    }
    """

    class Changed(Message):
        """Posted when the tag input value changes."""

        def __init__(self, tag_input: TagInput, value: str) -> None:
            super().__init__()
            self.tag_input = tag_input
            self.value = value

    def __init__(
        self,
        *,
        available_tags: list[str] | None = None,
        value: str = "",
        placeholder: str = "",
        id: str | None = None,
    ) -> None:
        """Initialize the TagInput widget.

        Args:
            available_tags: List of existing tags for suggestions.
            value: Initial value for the input field.
            placeholder: Placeholder text for the input field.
            id: Widget ID.
        """
        super().__init__(id=id)
        self._available_tags = available_tags or []
        self._initial_value = value
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        """Compose the input field and dropdown."""
        yield Input(
            value=self._initial_value,
            placeholder=self._placeholder,
            id="tag-text-input",
            valid_empty=True,
        )
        yield _NonFocusableOptionList(classes="_non-focusable-option-list")

    def on_mount(self) -> None:
        """Watch the inner Input's has_focus to show/hide dropdown."""
        input_widget = self.query_one("#tag-text-input", Input)
        self.watch(input_widget, "has_focus", self._on_input_focus_changed)

    def _on_input_focus_changed(self, has_focus: bool) -> None:
        """React to the inner Input gaining or losing focus."""
        if has_focus:
            self._update_suggestions()
        else:
            self._hide_dropdown()

    @property
    def value(self) -> str:
        """Get the current input text value."""
        try:
            return str(self.query_one("#tag-text-input", Input).value)
        except NoMatches:
            return self._initial_value

    @value.setter
    def value(self, new_value: str) -> None:
        """Set the input text value."""
        try:
            self.query_one("#tag-text-input", Input).value = new_value
        except NoMatches:
            self._initial_value = new_value

    @property
    def is_valid(self) -> bool:
        """Check if the current input is valid tag format."""
        text = self.value.strip()
        if not text:
            return True  # Empty is valid (optional field)
        return _TAG_PATTERN.match(text) is not None

    @property
    def valid_empty(self) -> bool:
        """Return True since tags are always optional."""
        return True

    def _is_input_focused(self) -> bool:
        """Check if the inner Input currently has focus."""
        try:
            return bool(self.query_one("#tag-text-input", Input).has_focus)
        except NoMatches:
            return False

    def _get_current_fragment(self) -> str:
        """Get the text fragment currently being typed (after last comma).

        Returns:
            The current fragment being typed, stripped of whitespace.
        """
        text = self.value
        if "," in text:
            return text.rsplit(",", 1)[1].strip()
        return text.strip()

    def _get_completed_tags(self) -> list[str]:
        """Get list of tags already completed (before the current fragment).

        Returns:
            List of tag strings already entered.
        """
        text = self.value
        if "," not in text:
            return []
        parts = text.rsplit(",", 1)[0]
        return [t.strip().lower() for t in parts.split(",") if t.strip()]

    def _filter_suggestions(self, fragment: str) -> list[str]:
        """Filter available tags based on the current fragment.

        Args:
            fragment: The current text fragment to match against.

        Returns:
            List of matching tag names, excluding already-entered tags.
        """
        completed = set(self._get_completed_tags())
        candidates = [
            tag for tag in self._available_tags if tag.lower() not in completed
        ]

        if not fragment:
            return candidates

        fragment_lower = fragment.lower()
        return [tag for tag in candidates if tag.lower().startswith(fragment_lower)]

    def _show_dropdown(self, suggestions: list[str]) -> None:
        """Show the dropdown with given suggestions.

        Args:
            suggestions: List of tag names to display.
        """
        option_list = self.query_one(_NonFocusableOptionList)
        option_list.clear_options()
        if not suggestions:
            option_list.remove_class("visible")
            return
        for tag in suggestions:
            option_list.add_option(Option(tag))
        option_list.add_class("visible")
        option_list.highlighted = 0

    def _hide_dropdown(self) -> None:
        """Hide the suggestion dropdown."""
        option_list = self.query_one(_NonFocusableOptionList)
        option_list.remove_class("visible")

    def _is_dropdown_visible(self) -> bool:
        """Check if the dropdown is currently visible."""
        option_list = self.query_one(_NonFocusableOptionList)
        return bool(option_list.has_class("visible"))

    def _accept_suggestion(self) -> None:
        """Accept the currently highlighted suggestion."""
        option_list = self.query_one(_NonFocusableOptionList)
        highlighted = option_list.highlighted
        if highlighted is None:
            return

        option = option_list.get_option_at_index(highlighted)
        selected_tag = option.prompt
        if not isinstance(selected_tag, str) or not selected_tag:
            return

        # Build new value: completed tags + selected tag + trailing comma
        # Use lower() to match _get_completed_tags() for consistent dedup
        completed = self._get_completed_tags()
        completed.append(selected_tag.lower())
        new_value = ",".join(completed) + ","

        input_widget = self.query_one("#tag-text-input", Input)
        input_widget.value = new_value
        input_widget.cursor_position = len(new_value)

        self._hide_dropdown()

    def _update_suggestions(self) -> None:
        """Update the dropdown suggestions based on current input.

        Only shows suggestions when the inner Input has focus.
        """
        if not self._available_tags or not self._is_input_focused():
            return

        fragment = self._get_current_fragment()
        suggestions = self._filter_suggestions(fragment)
        self._show_dropdown(suggestions)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input text changes."""
        if event.input.id == "tag-text-input":
            event.stop()
            self._update_suggestions()
            self.post_message(self.Changed(self, event.value))

    def on_key(self, event: Key) -> None:
        """Handle keyboard events for dropdown navigation."""
        if not self._is_dropdown_visible():
            return  # Let all keys propagate normally

        option_list = self.query_one(_NonFocusableOptionList)

        if event.key == "down":
            event.stop()
            event.prevent_default()
            option_list.action_cursor_down()
        elif event.key == "up":
            event.stop()
            event.prevent_default()
            option_list.action_cursor_up()
        elif event.key in ("enter", "tab"):
            event.stop()
            event.prevent_default()
            self._accept_suggestion()
        elif event.key == "escape":
            event.stop()
            event.prevent_default()
            self._hide_dropdown()

    def focus(self, scroll_visible: bool = True) -> None:  # type: ignore[override]
        """Focus the inner Input widget."""
        try:
            self.query_one("#tag-text-input", Input).focus(scroll_visible)
        except NoMatches:
            super().focus(scroll_visible)
