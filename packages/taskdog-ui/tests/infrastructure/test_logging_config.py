"""Tests for TUI file-based logging configuration."""

import logging
import os
from logging.handlers import RotatingFileHandler
from unittest.mock import patch

from taskdog.infrastructure.logging_config import (
    LOG_FILE_NAME,
    configure_tui_logging,
)


class TestConfigureTuiLogging:
    """configure_tui_logging routes taskdog logs to a state-dir file."""

    def _cleanup(self) -> None:
        for name in ("taskdog", "taskdog_core"):
            log = logging.getLogger(name)
            for h in [h for h in log.handlers if getattr(h, "_taskdog_tui", False)]:
                log.removeHandler(h)

    def test_writes_to_state_dir_file(self, tmp_path):
        with patch.dict(os.environ, {"XDG_STATE_HOME": str(tmp_path)}):
            log_file = configure_tui_logging()
        try:
            assert log_file == tmp_path / "taskdog" / LOG_FILE_NAME

            logging.getLogger("taskdog.test").error("boom")
            for h in logging.getLogger("taskdog").handlers:
                h.flush()

            assert log_file.exists()
            assert "boom" in log_file.read_text(encoding="utf-8")
        finally:
            self._cleanup()

    def test_no_stream_handler_installed(self, tmp_path):
        """The TUI owns the terminal: only a file handler may be attached."""
        with patch.dict(os.environ, {"XDG_STATE_HOME": str(tmp_path)}):
            configure_tui_logging()
        try:
            handlers = logging.getLogger("taskdog").handlers
            tui_handlers = [h for h in handlers if getattr(h, "_taskdog_tui", False)]
            assert tui_handlers
            assert all(isinstance(h, RotatingFileHandler) for h in tui_handlers)
        finally:
            self._cleanup()

    def test_idempotent_no_duplicate_handlers(self, tmp_path):
        with patch.dict(os.environ, {"XDG_STATE_HOME": str(tmp_path)}):
            configure_tui_logging()
            configure_tui_logging()
        try:
            handlers = logging.getLogger("taskdog").handlers
            tui_handlers = [h for h in handlers if getattr(h, "_taskdog_tui", False)]
            assert len(tui_handlers) == 1
        finally:
            self._cleanup()

    def test_respects_level_argument(self, tmp_path):
        with patch.dict(os.environ, {"XDG_STATE_HOME": str(tmp_path)}):
            configure_tui_logging(level="DEBUG")
        try:
            assert logging.getLogger("taskdog").level == logging.DEBUG
        finally:
            self._cleanup()
