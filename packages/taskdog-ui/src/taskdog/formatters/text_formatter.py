"""Text formatting utilities for terminal display."""

from rich.markup import escape

from taskdog.constants.common import COLUMN_FINISHED_STYLE


def format_finished_name(name: str, is_finished: bool) -> str:
    """Escape Rich markup in the name and apply strikethrough if finished."""
    escaped = escape(name)
    if is_finished:
        return f"[{COLUMN_FINISHED_STYLE}]{escaped}[/{COLUMN_FINISHED_STYLE}]"
    return escaped
