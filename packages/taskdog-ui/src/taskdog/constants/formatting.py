"""Table title formatting utility."""

from taskdog.constants.common import TABLE_TITLE_COLOR


def format_table_title(title: str) -> str:
    """Format table title with standard styling.

    Args:
        title: The title text to format

    Returns:
        Formatted title string with Rich markup
    """
    return f"[{TABLE_TITLE_COLOR}]{title}[/{TABLE_TITLE_COLOR}]"
