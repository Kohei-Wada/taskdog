"""MCP server for Taskdog.

This package provides a Model Context Protocol (MCP) server that enables
Claude Desktop and other MCP-compatible AI clients to interact with Taskdog.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("taskdog-mcp")
except PackageNotFoundError:
    __version__ = "unknown"
