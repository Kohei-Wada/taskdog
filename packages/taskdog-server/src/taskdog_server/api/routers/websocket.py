"""WebSocket router for real-time task updates.

This module provides WebSocket endpoints for clients to receive
real-time notifications about task changes.
"""

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from taskdog_server.api.dependencies import ConnectionManagerWsDep

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    manager: ConnectionManagerWsDep,
) -> None:
    """WebSocket endpoint for real-time task updates.

    Clients connect to this endpoint to receive real-time notifications
    when tasks are created, updated, or deleted.

    Args:
        websocket: The WebSocket connection

    Message Format:
        {
            "type": "task_created" | "task_updated" | "task_deleted" | "task_status_changed",
            "task_id": int,
            "task_name": str,
            "data": {...}  # Full task data or relevant fields
        }
    """
    # Generate unique client ID for this connection
    client_id = str(uuid.uuid4())

    # Get user name from X-User-Name header
    # This should be set by reverse proxy (e.g., Kong's request-transformer plugin)
    user_name = websocket.headers.get("x-user-name")
    # Sanitize user name to prevent log injection attacks (CWE-117)
    if user_name:
        user_name = user_name.strip()[:100]  # Limit length and strip whitespace

    await manager.connect(client_id, websocket, user_name)
    try:
        # Send welcome message with client ID and user name
        await manager.send_personal_message(
            {
                "type": "connected",
                "message": "Connected to Taskdog real-time updates",
                "client_id": client_id,
                "user_name": user_name,
                "connections": manager.get_connection_count(),
            },
            client_id,
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages (for future two-way communication)
            data = await websocket.receive_json()

            # Handle ping/pong for keepalive
            if data.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": data.get("timestamp")}, client_id
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        manager.disconnect(client_id)
