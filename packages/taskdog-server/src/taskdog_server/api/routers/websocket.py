"""WebSocket router for real-time task updates.

This module provides WebSocket endpoints for clients to receive
real-time notifications about task changes.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from taskdog_server.api.dependencies import get_connection_manager
from taskdog_server.websocket.connection_manager import ConnectionManager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
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

    await manager.connect(client_id, websocket)
    try:
        # Send welcome message with client ID
        await manager.send_personal_message(
            {
                "type": "connected",
                "message": "Connected to Taskdog real-time updates",
                "client_id": client_id,
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
