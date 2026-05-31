"""Editor utilities for opening files in user's preferred editor."""

import os
import platform
import shutil


def _fallback_editors() -> list[str]:
    """Return platform-appropriate editor fallbacks."""
    if platform.system() == "Windows":
        return ["code", "notepad", "vim"]
    return ["vim", "nano", "vi"]


def get_editor() -> str:
    """Get editor command from environment or fallback to defaults.

    Returns:
        str: Editor command (e.g., 'vim', 'nano', 'vi')

    Raises:
        RuntimeError: If no editor is found
    """
    # Try $EDITOR first
    editor = os.getenv("EDITOR")
    if editor:
        return editor

    # Fallback to common editors
    fallbacks = _fallback_editors()
    for fallback in fallbacks:
        if shutil.which(fallback):
            return fallback

    # No editor found
    raise RuntimeError(
        "No editor found. Please set $EDITOR environment variable "
        f"or install one of: {', '.join(fallbacks)}."
    )
