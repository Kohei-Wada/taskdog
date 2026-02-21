"""taskdog - CLI task management tool"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("taskdog-ui")
except PackageNotFoundError:
    __version__ = "unknown"
