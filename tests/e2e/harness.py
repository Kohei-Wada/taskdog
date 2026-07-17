"""Helpers for spawning a production taskdog-server subprocess in E2E tests.

Kept out of conftest.py so both the fixtures and individual test modules can
import spawn_server without relying on pytest's conftest import machinery.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from typing import TYPE_CHECKING

from taskdog_client.taskdog_api_client import TaskdogApiClient

if TYPE_CHECKING:
    from pathlib import Path

_READINESS_TIMEOUT_S = 15.0


def _free_port() -> int:
    """Reserve an ephemeral TCP port and release it for the server to bind."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(base_url: str, process: subprocess.Popen[bytes]) -> None:
    """Poll /health until the server responds or the timeout elapses."""
    probe = TaskdogApiClient(base_url=base_url)
    deadline = time.monotonic() + _READINESS_TIMEOUT_S
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(
                    f"server exited early with code {process.returncode}"
                )
            if probe.check_health():
                return
            time.sleep(0.1)
        raise RuntimeError("server did not become healthy in time")
    finally:
        probe.close()


def spawn_server(
    db_path: Path, cfg_dir: Path, *, auth: bool
) -> tuple[subprocess.Popen[bytes], str]:
    """Launch a taskdog-server subprocess and wait until it is healthy.

    Args:
        db_path: SQLite file the server should use.
        cfg_dir: Empty XDG_CONFIG_HOME so host config never leaks in.
        auth: When True, enable auth via env override.

    Returns:
        (process, base_url).
    """
    port = _free_port()
    env = {
        **os.environ,
        "TASKDOG_STORAGE_DATABASE_URL": f"sqlite:///{db_path}",
        "XDG_CONFIG_HOME": str(cfg_dir),
    }
    if auth:
        env["TASKDOG_AUTH_ENABLED"] = "true"
    # Redirect server output to a file rather than a PIPE: an unread PIPE
    # deadlocks the server once the OS buffer fills with access logs, while
    # DEVNULL would discard the diagnostics we need when startup fails.
    log_path = db_path.parent / "server.log"
    with log_path.open("w") as log_file:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "taskdog_server.main",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_ready(base_url, process)
    except Exception as exc:
        if process.poll() is None:
            terminate_server(process)
        raise RuntimeError(
            f"taskdog-server failed to start (log at {log_path}):\n"
            f"{log_path.read_text()[-2000:]}"
        ) from exc
    return process, base_url


def terminate_server(process: subprocess.Popen[bytes]) -> None:
    """Terminate a spawned server process, escalating to kill if needed."""
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
