"""Text formatting utilities for terminal display."""

from rich.markup import escape

from taskdog.constants.common import COLUMN_FINISHED_STYLE
from taskdog.constants.symbols import EMOJI_FIXED, EMOJI_NOTE

# Shown when a value-less column (tags, dependencies, flags) is empty.
EMPTY_FIELD_PLACEHOLDER = "-"


def format_finished_name(name: str, is_finished: bool) -> str:
    """Escape Rich markup in the name and apply strikethrough if finished."""
    escaped = escape(name)
    if is_finished:
        return f"[{COLUMN_FINISHED_STYLE}]{escaped}[/{COLUMN_FINISHED_STYLE}]"
    return escaped


def format_tags(tags: list[str] | None) -> str:
    """Format task tags as a comma-separated string, or the empty placeholder."""
    if not tags:
        return EMPTY_FIELD_PLACEHOLDER
    return ", ".join(tags)


def format_dependencies(depends_on: list[int] | None) -> str:
    """Format task dependencies as a comma-separated string, or the placeholder."""
    if not depends_on:
        return EMPTY_FIELD_PLACEHOLDER
    return ",".join(str(dep_id) for dep_id in depends_on)


def format_flags(is_fixed: bool, has_notes: bool) -> str:
    """Format task flag indicators (fixed + notes).

    Icon columns show nothing when no flag applies (the absence is the signal),
    unlike list columns which use EMPTY_FIELD_PLACEHOLDER.
    """
    indicators = ""
    if is_fixed:
        indicators += EMOJI_FIXED
    if has_notes:
        indicators += EMOJI_NOTE
    return indicators
