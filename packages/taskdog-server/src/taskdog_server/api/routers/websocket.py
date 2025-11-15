"""WebSocket router for real-time task updates.

This module provides WebSocket endpoints for clients to receive
real-time notifications about task changes.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from taskdog_server.websocket.connection_manager import ConnectionManager

router = APIRouter()

# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
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
    await manager.connect(websocket)
    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connected",
                "message": "Connected to Taskdog real-time updates",
                "connections": manager.get_connection_count(),
            },
            websocket,
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages (for future two-way communication)
            data = await websocket.receive_json()

            # Handle ping/pong for keepalive
            if data.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": data.get("timestamp")}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance.

    Returns:
        The connection manager instance
    """
    return manager
