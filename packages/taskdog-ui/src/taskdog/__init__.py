"""taskdog - CLI task management tool"""

from importlib.metadata import version

try:
    __version__ = version("taskdog-ui")
except Exception:
    __version__ = "unknown"
