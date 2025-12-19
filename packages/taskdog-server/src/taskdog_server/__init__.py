"""Taskdog API Server.

FastAPI-based REST API server for task management.
"""

from importlib.metadata import version

try:
    __version__ = version("taskdog-server")
except Exception:
    __version__ = "unknown"
