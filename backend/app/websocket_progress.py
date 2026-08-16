import asyncio
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ProgressWebSocketManager:
    """
    WebSocket Connection Manager for streaming real-time progress updates
    during document parsing, section-by-section rewriting, plagiarism scanning, and peer review.
    """

    def __init__(self):
        # Maps paper_id to list of active WebSocket connection objects
        self.active_connections: Dict[str, List[Any]] = {}

    async def connect(self, paper_id: str, websocket: Any):
        """Accepts WebSocket connection and tracks it under paper_id."""
        await websocket.accept()
        if paper_id not in self.active_connections:
            self.active_connections[paper_id] = []
        self.active_connections[paper_id].append(websocket)
        logger.info(f"WebSocket client connected for paper {paper_id}")

    def disconnect(self, paper_id: str, websocket: Any):
        """Removes a disconnected WebSocket client."""
        if paper_id in self.active_connections:
            if websocket in self.active_connections[paper_id]:
                self.active_connections[paper_id].remove(websocket)
            if not self.active_connections[paper_id]:
                del self.active_connections[paper_id]

    async def broadcast_progress(self, paper_id: str, step: str, progress_pct: int, message: str, extra_data: Dict[str, Any] = None):
        """Broadcasts a JSON progress event payload to all clients connected to paper_id."""
        if paper_id not in self.active_connections:
            return

        payload = {
            "paper_id": paper_id,
            "step": step,
            "progress_pct": min(max(progress_pct, 0), 100),
            "message": message,
            "extra_data": extra_data or {}
        }

        dead_connections = []
        for connection in self.active_connections[paper_id]:
            try:
                await connection.send_text(json.dumps(payload))
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(paper_id, dead)


# Global WebSocket manager instance
progress_ws_manager = ProgressWebSocketManager()
