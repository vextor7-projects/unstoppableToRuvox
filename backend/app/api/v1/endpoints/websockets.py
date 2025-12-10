import uuid
import logging
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from redis.asyncio import Redis

from app.services.websocket_service import websocket_manager
from app.api.v1.deps import get_current_active_user
from app.core.config import settings
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Ticket Mechanism for Secure Handshake ---

@router.post("/auth/ticket", response_model=dict)
async def create_websocket_ticket(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate a short-lived, one-time ticket for WebSocket connection.
    This prevents passing the JWT in the WebSocket URL query params.
    """
    ticket = str(uuid.uuid4())
    redis = Redis.from_url(str(settings.REDIS_URL), decode_responses=True)
    
    # Store ticket with user_id, expires in 30 seconds
    await redis.setex(f"ws_ticket:{ticket}", 30, str(current_user.id))
    await redis.close()
    
    return {"ticket": ticket}

# --- WebSocket Endpoints ---

@router.websocket("/user/events")
async def websocket_user_events(
    websocket: WebSocket,
    ticket: str = Query(..., description="One-time ticket from /auth/ticket"),
):
    """
    WebSocket endpoint for authenticated user events.
    """
    # 1. Validate Ticket
    redis = Redis.from_url(str(settings.REDIS_URL), decode_responses=True)
    user_id_str = await redis.get(f"ws_ticket:{ticket}")
    
    # Consume the ticket (One-time use)
    if user_id_str:
        await redis.delete(f"ws_ticket:{ticket}")
    await redis.close()

    if not user_id_str:
        await websocket.close(code=1008, reason="Invalid or expired ticket")
        return

    try:
        user_id = uuid.UUID(user_id_str)
        # 2. Connect
        await websocket_manager.connect_user(websocket, user_id)
        
        while True:
            # Keep alive loop
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        websocket_manager.disconnect_user(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass


@router.websocket("/payment/session/{session_id}")
async def websocket_payment_session(
    websocket: WebSocket,
    session_id: str,
):
    """
    Public endpoint for monitoring payment sessions (e.g., POS Terminal).
    """
    # Note: For strict security, we could require a ticket here too, 
    # but payment sessions are often ephemeral and public-facing (QR scan confirmation).
    # We rely on the unpredictability of the UUID session_id.
    
    await websocket_manager.connect_session(websocket, session_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect_session(websocket, session_id)