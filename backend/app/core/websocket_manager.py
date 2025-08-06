import json
from typing import Any, Dict, List

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: " f"{len(self.active_connections)}")  # Debug print
        if websocket.client:
            print(f"Connection details: " f"{websocket.client.host}:{websocket.client.port}")  # Debug print

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket disconnected. Total connections: " f"{len(self.active_connections)}")  # Debug print

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        print(f"Broadcasting to {len(self.active_connections)} " f"connections: {message}")  # Debug print
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to connection: {e}")  # Debug print
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def send_progress_update(self, task_id: str, progress: int, status: str, message: str = "") -> None:
        """Send progress update to all connected clients"""
        await self.broadcast(
            {
                "type": "progress_update",
                "task_id": task_id,
                "progress": progress,
                "status": status,
                "message": message,
            }
        )

    async def send_processing_complete(self, task_id: str, document_id: str) -> None:
        """Send processing complete notification"""
        await self.broadcast(
            {
                "type": "processing_complete",
                "task_id": task_id,
                "document_id": document_id,
            }
        )

    async def send_error(self, task_id: str, error_message: str) -> None:
        """Send error notification"""
        message = {"type": "error", "task_id": task_id, "error": error_message}
        print(f"Broadcasting error message: {message}")  # Debug print
        await self.broadcast(message)

    async def send_document_deletion_started(self, document_id: str) -> None:
        """Send document deletion started notification"""
        await self.broadcast(
            {
                "type": "document_deletion_started",
                "document_id": document_id,
            }
        )

    async def send_document_deleted_success(self, document_id: str) -> None:
        """Send document deletion success notification"""
        await self.broadcast(
            {
                "type": "document_deleted_success",
                "document_id": document_id,
            }
        )

    async def send_document_deleted_failed(self, document_id: str, error_message: str) -> None:
        """Send document deletion failed notification"""
        await self.broadcast(
            {
                "type": "document_deleted_failed",
                "document_id": document_id,
                "error": error_message,
            }
        )
