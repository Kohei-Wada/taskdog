"""Background server management for Taskdog API."""

import atexit
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from taskdog_core.shared.xdg_utils import XDGDirectories


class ServerManager:
    """Manages the background FastAPI server lifecycle.

    This class handles starting, stopping, and monitoring a background
    FastAPI server process. It ensures only one server instance runs
    at a time using PID files and port checking.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        """Initialize server manager.

        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        data_dir = XDGDirectories.get_data_home()
        self.pid_file = data_dir / "server.pid"
        self.log_file = data_dir / "server.log"
        self.process: subprocess.Popen | None = None

    def is_port_in_use(self) -> bool:
        """Check if the server port is already in use.

        Returns:
            True if port is in use, False otherwise
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((self.host, self.port))
                return False
            except OSError:
                return True

    def is_server_running(self) -> bool:
        """Check if a server is already running.

        Checks both the PID file and port availability.

        Returns:
            True if server is running, False otherwise
        """
        # Check if PID file exists and process is alive
        if self.pid_file.exists():
            try:
                with open(self.pid_file) as f:
                    pid = int(f.read().strip())

                # Check if process exists
                try:
                    os.kill(pid, 0)  # Signal 0 doesn't kill, just checks
                    return True
                except OSError:
                    # Process doesn't exist, clean up stale PID file
                    self.pid_file.unlink()
                    return False
            except (OSError, ValueError):
                return False

        # Fallback: check if port is in use
        return self.is_port_in_use()

    def start(self, wait_for_startup: bool = True, timeout: float = 10.0) -> bool:
        """Start the background server.

        Args:
            wait_for_startup: Wait for server to be ready
            timeout: Maximum time to wait for startup (seconds)

        Returns:
            True if server started successfully, False otherwise
        """
        # Check if server is already running
        if self.is_server_running():
            return True

        # Ensure directories exist
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Start server process
        try:
            # Open log file for output
            with open(self.log_file, "w") as log_handle:
                # Find the taskdog executable
                taskdog_cmd = self._find_taskdog_command()

                # Start server in background
                self.process = subprocess.Popen(
                    [
                        taskdog_cmd,
                        "server",
                        "--host",
                        self.host,
                        "--port",
                        str(self.port),
                    ],
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,  # Detach from parent
                )

            # Write PID file
            with open(self.pid_file, "w") as f:
                f.write(str(self.process.pid))

            # Register cleanup
            atexit.register(self.stop)

            # Wait for server to be ready
            if wait_for_startup and not self._wait_for_server(timeout):
                self.stop()
                return False

            return True

        except Exception as e:
            print(f"Failed to start server: {e}", file=sys.stderr)
            return False

    def _find_taskdog_command(self) -> str:
        """Find the taskdog command path.

        Returns:
            Path to taskdog executable

        Raises:
            RuntimeError: If taskdog command not found
        """
        # Try to find taskdog in PATH
        import shutil

        taskdog_path = shutil.which("taskdog")
        if taskdog_path:
            return taskdog_path

        # Try current Python environment
        python_dir = Path(sys.executable).parent
        taskdog_local = python_dir / "taskdog"
        if taskdog_local.exists():
            return str(taskdog_local)

        raise RuntimeError("taskdog command not found. Please install taskdog first.")

    def _wait_for_server(self, timeout: float) -> bool:
        """Wait for server to be ready.

        Args:
            timeout: Maximum time to wait (seconds)

        Returns:
            True if server is ready, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Try to connect to server
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1.0)
                    sock.connect((self.host, self.port))
                    return True
            except (OSError, ConnectionRefusedError):
                time.sleep(0.1)
                continue

        return False

    def stop(self) -> None:
        """Stop the background server."""
        # Try to stop the process we started
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None

        # Try to stop server using PID file
        if self.pid_file.exists():
            try:
                with open(self.pid_file) as f:
                    pid = int(f.read().strip())

                try:
                    os.kill(pid, signal.SIGTERM)
                    # Wait a bit for graceful shutdown
                    time.sleep(0.5)
                    # Check if still alive
                    try:
                        os.kill(pid, 0)
                        # Still alive, force kill
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass  # Process already dead
                except OSError:
                    pass  # Process doesn't exist

                # Remove PID file
                self.pid_file.unlink()
            except (OSError, ValueError):
                pass

    def __enter__(self) -> "ServerManager":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.stop()
