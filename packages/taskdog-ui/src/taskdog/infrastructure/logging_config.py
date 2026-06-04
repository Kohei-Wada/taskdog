"""File-based logging configuration for the Taskdog TUI.

A Textual TUI owns stdout/stderr, so logging there would corrupt the display.
Instead, taskdog/taskdog_core log records are routed to a rotating file under
the XDG state directory, where they can be inspected after the fact.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from taskdog_core.shared.xdg_utils import XDGDirectories

LOG_FILE_NAME = "tui.log"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 3
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Logger namespaces whose records should reach the TUI log file.
_TARGET_LOGGERS = ("taskdog", "taskdog_core")


def configure_tui_logging(level: str | None = None) -> Path:
    """Route taskdog log records to a rotating file under the state dir.

    No stream handler is installed: the TUI controls the terminal, so anything
    written to stdout/stderr would break the display.

    Args:
        level: Log level name (e.g. "DEBUG"). Defaults to env var
            ``TASKDOG_LOG_LEVEL`` or "INFO".

    Returns:
        Path to the active log file.
    """
    log_level_str = (level or os.getenv("TASKDOG_LOG_LEVEL") or "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    log_file = XDGDirectories.get_state_home() / LOG_FILE_NAME
    handler = RotatingFileHandler(
        log_file,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler._taskdog_tui = True  # type: ignore[attr-defined]  # tag for idempotency

    for name in _TARGET_LOGGERS:
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        # Idempotent: drop any handler a previous call attached.
        for existing in [
            h for h in logger.handlers if getattr(h, "_taskdog_tui", False)
        ]:
            logger.removeHandler(existing)
        logger.addHandler(handler)

    return log_file
