"""WebSocket endpoint for real-time training progress."""
import asyncio
import logging
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app.core.db import engine

router = APIRouter()
logger = logging.getLogger(__name__)

# Global dict to store active WebSocket connections per experiment
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/experiments/{experiment_id}/progress")
async def experiment_progress_stream(websocket: WebSocket, experiment_id: str):
    """Stream real-time training progress via WebSocket."""
    await websocket.accept()
    active_connections[experiment_id] = websocket
    logger.info(f"WebSocket connected for experiment {experiment_id}")
    
    try:
        # Keep connection alive and listen for client messages
        while True:
            # Wait for any message from client (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for experiment {experiment_id}")
        active_connections.pop(experiment_id, None)
    except Exception as e:
        logger.error(f"WebSocket error for experiment {experiment_id}: {e}")
        active_connections.pop(experiment_id, None)


async def broadcast_progress(experiment_id: str, message: dict):
    """Broadcast progress update to connected WebSocket client."""
    if experiment_id in active_connections:
        try:
            await active_connections[experiment_id].send_json(message)
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")
            active_connections.pop(experiment_id, None)

# Made with Bob
