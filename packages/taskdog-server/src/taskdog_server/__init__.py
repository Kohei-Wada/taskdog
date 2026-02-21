"""Taskdog API Server.

FastAPI-based REST API server for task management.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("taskdog-server")
except PackageNotFoundError:
    __version__ = "unknown"
