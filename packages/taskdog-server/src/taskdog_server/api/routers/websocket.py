"""WebSocket router for real-time task updates.

This module provides WebSocket endpoints for clients to receive
real-time notifications about task changes.
"""

import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from taskdog_server.api.dependencies import (
    ConnectionManagerWsDep,
    ServerConfigWsDep,
    validate_api_key_for_websocket,
)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    manager: ConnectionManagerWsDep,
    server_config: ServerConfigWsDep,
    token: str | None = Query(None, description="API key for authentication"),
) -> None:
    """WebSocket endpoint for real-time task updates.

    Clients connect to this endpoint to receive real-time notifications
    when tasks are created, updated, or deleted.

    Authentication:
        Pass API key as query parameter: /ws?token=sk-xxx

    Args:
        websocket: The WebSocket connection
        manager: Connection manager dependency
        server_config: Server configuration dependency
        token: API key for authentication (query parameter)

    Message Format:
        {
            "type": "task_created" | "task_updated" | "task_deleted" | "task_status_changed",
            "task_id": int,
            "task_name": str,
            "data": {...}  # Full task data or relevant fields
        }
    """
    # Validate API key before accepting connection
    try:
        client_name = validate_api_key_for_websocket(token, server_config)
    except ValueError as e:
        await websocket.close(code=4001, reason=str(e))
        return

    # Generate unique client ID for this connection
    client_id = str(uuid.uuid4())

    # Use authenticated client name, or "anonymous" if auth is disabled
    user_name = client_name if client_name else "anonymous"

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
