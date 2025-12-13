"""Entry point for the Taskdog MCP server.

Run with: taskdog-mcp
Or: python -m taskdog_mcp.main
"""

import argparse

from taskdog_mcp import __version__
from taskdog_mcp.server import create_mcp_server


def main() -> None:
    """Start the MCP server."""
    parser = argparse.ArgumentParser(
        description="Taskdog MCP Server - Model Context Protocol server for AI integration",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"taskdog-mcp {__version__}",
    )
    # Parse args (exits on --version)
    parser.parse_args()

    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
