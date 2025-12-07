"""Entry point for the Taskdog MCP server.

Run with: taskdog-mcp
Or: python -m taskdog_mcp.main
"""

from taskdog_mcp.server import create_mcp_server


def main() -> None:
    """Start the MCP server."""
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
