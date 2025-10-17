"""Editor utilities for opening files in user's preferred editor."""

import os
import subprocess


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
    for fallback in ["vim", "nano", "vi"]:
        # Check if editor exists in PATH
        try:
            subprocess.run(
                ["which", fallback],
                check=True,
                capture_output=True,
                text=True,
            )
            return fallback
        except subprocess.CalledProcessError:
            continue

    # No editor found
    raise RuntimeError(
        "No editor found. Please set $EDITOR environment variable or install vim, nano, or vi."
    )
