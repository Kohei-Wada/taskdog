"""TUI command - Launch the Text User Interface."""

from urllib.parse import urlparse, urlunparse

import click

from taskdog.cli.context import CliContext
from taskdog.infrastructure.websocket import WebSocketClient
from taskdog.tui.app import TaskdogTUI


def _get_websocket_url(base_url: str) -> str:
    """Get WebSocket URL from API base URL.

    Args:
        base_url: API base URL (e.g., "http://127.0.0.1:8000")

    Returns:
        WebSocket URL (e.g., "ws://127.0.0.1:8000/ws")
    """
    parsed = urlparse(base_url)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    ws_parsed = parsed._replace(scheme=ws_scheme)
    return f"{urlunparse(ws_parsed)}/ws"


@click.command(
    name="tui", help="Launch the Text User Interface for interactive task management."
)
@click.pass_context
def tui_command(ctx: click.Context) -> None:
    """Launch the TUI for interactive task management.

    The TUI provides a full-screen interface with keyboard shortcuts:
    - ↑/↓: Navigate tasks
    - s: Start selected task
    - d: Complete selected task
    - a: Add new task
    - Delete: Remove selected task
    - Enter: Show task details
    - r: Refresh task list
    - q: Quit

    TUI now requires an API client connection (same as all other CLI commands).
    """
    ctx_obj: CliContext = ctx.obj
    api_client = ctx_obj.api_client
    cli_config = ctx_obj.config

    # Initialize WebSocket client for real-time updates
    ws_url = _get_websocket_url(api_client.base_url)
    websocket_client = WebSocketClient(ws_url=ws_url, api_key=api_client.api_key)

    # Launch the TUI application with all dependencies injected
    app = TaskdogTUI(
        api_client=api_client,
        websocket_client=websocket_client,
        cli_config=cli_config,
    )
    app.run()
