"""ASCII art and branding constants for Taskdog."""

from rich.console import Console

# Modern box-drawing wordmark (pyfiglet "future" font) shown at the top of
# `taskdog --help` and the TUI help dialog. The small face keeps the dog
# motif from the name while matching the clean look of the Textual TUI.
TASKDOG_WORDMARK = r"""  ╺┳╸┏━┓┏━┓╻┏ ╺┳┓┏━┓┏━╸
   ┃ ┣━┫┗━┓┣┻┓ ┃┃┃ ┃┃╺┓   ⊙ᴥ⊙
   ╹ ╹ ╹┗━┛╹ ╹╺┻┛┗━┛┗━┛"""

# Fallback for terminals that cannot render box-drawing / unicode glyphs.
TASKDOG_WORDMARK_ASCII = "  taskdog"

TASKDOG_TAGLINE = "Local-first task management, done in your terminal"


def print_banner(console: Console) -> None:
    """Print the branded header for `taskdog --help`.

    Uses the unicode wordmark on UTF-8 terminals and a plain-text fallback
    elsewhere, so the banner degrades gracefully without unicode.
    """
    supports_unicode = "utf" in (console.encoding or "").lower()
    wordmark = TASKDOG_WORDMARK if supports_unicode else TASKDOG_WORDMARK_ASCII
    console.print(wordmark, style="bold cyan", highlight=False)
    console.print(f"  {TASKDOG_TAGLINE}", style="dim")
    console.print()
