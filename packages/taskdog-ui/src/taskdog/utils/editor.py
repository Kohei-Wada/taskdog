"""Editor utilities for opening files in user's preferred editor."""

import os
import shutil
import sys


def get_editor() -> str:
    """Get editor command from environment or fallback to defaults.

    On Windows, defaults to common Windows editors (code, notepad++, notepad).
    On Unix, defaults to vim, nano, vi.

    Returns:
        str: Editor command (e.g., 'vim', 'nano', 'code', 'notepad')

    Raises:
        RuntimeError: If no editor is found
    """
    # Try $EDITOR first (works on all platforms)
    editor = os.getenv("EDITOR")
    if editor:
        return editor

    # Platform-specific fallbacks
    if sys.platform == "win32":
        fallbacks = ["code", "notepad++", "notepad"]
    else:
        fallbacks = ["vim", "nano", "vi"]

    # Use shutil.which() for cross-platform editor detection
    for fallback in fallbacks:
        if shutil.which(fallback):
            return fallback

    # Final fallback for Windows - notepad is always available
    if sys.platform == "win32":
        return "notepad"

    # No editor found on Unix
    raise RuntimeError(
        "No editor found. Please set $EDITOR environment variable or install vim, nano, or vi."
    )
