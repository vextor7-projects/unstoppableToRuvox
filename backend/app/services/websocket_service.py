import logging
import json
import uuid
import asyncio
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

class WebSocketService:
    """
    Manages WebSocket connections with Redis Pub/Sub for horizontal scalability.
    
    Architecture:
    1. User connects -> Server subscribes to Redis channel 'ws:user:{user_id}'
    2. Event occurs -> Service publishes to Redis channel 'ws:user:{user_id}'
    3. Server receives Redis message -> Forwards to local WebSocket connection
    """
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebSocketService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Local connections: map user_id -> set of WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.session_connections: Dict[str, Set[WebSocket]] = {}
        
        # Redis connection for Pub/Sub
        self.redis: Optional[Redis] = None
        self.pubsub = None
        self.listen_task = None

    async def start(self):
        """Called on app startup to initialize Redis listener."""
        self.redis = Redis.from_url(str(settings.REDIS_URL), decode_responses=True)
        self.pubsub = self.redis.pubsub()
        # Start the background listener loop
        self.listen_task = asyncio.create_task(self._redis_listener())
        logger.info("WebSocket Service started with Redis Pub/Sub.")

    async def stop(self):
        """Called on app shutdown."""
        if self.listen_task:
            self.listen_task.cancel()
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    async def connect_user(self, websocket: WebSocket, user_id: uuid.UUID):
        """Register a user connection and subscribe to their Redis channel."""
        await websocket.accept()
        uid_str = str(user_id)
        
        if uid_str not in self.active_connections:
            self.active_connections[uid_str] = set()
            # Subscribe to this user's channel if not already watched by this instance
            await self.pubsub.subscribe(f"ws:user:{uid_str}")
            
        self.active_connections[uid_str].add(websocket)
        logger.info(f"User connected: {uid_str}")

    def disconnect_user(self, websocket: WebSocket, user_id: uuid.UUID):
        """Remove connection and unsubscribe if no sessions left."""
        uid_str = str(user_id)
        if uid_str in self.active_connections:
            self.active_connections[uid_str].discard(websocket)
            if not self.active_connections[uid_str]:
                del self.active_connections[uid_str]
                # We can unsubscribe from Redis to save resources, 
                # strictly speaking, we need to handle this via the async loop safely
                # usually we just leave it or queue an unsubscribe task.
                asyncio.create_task(self.pubsub.unsubscribe(f"ws:user:{uid_str}"))

    async def connect_session(self, websocket: WebSocket, session_id: str):
        """Register a payment session monitor."""
        await websocket.accept()
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
            await self.pubsub.subscribe(f"ws:session:{session_id}")
            
        self.session_connections[session_id].add(websocket)

    def disconnect_session(self, websocket: WebSocket, session_id: str):
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
                asyncio.create_task(self.pubsub.unsubscribe(f"ws:session:{session_id}"))

    async def send_to_user(self, user_id: uuid.UUID, message: Dict[str, Any]):
        """
        Publish a message to the user's Redis channel.
        Any server instance holding a connection for this user will pick it up.
        """
        if not self.redis:
            logger.error("Redis not initialized in WebSocketService")
            return

        channel = f"ws:user:{str(user_id)}"
        await self.redis.publish(channel, json.dumps(message))

    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        """Publish to a payment session channel."""
        if not self.redis:
            return
            
        channel = f"ws:session:{session_id}"
        await self.redis.publish(channel, json.dumps(message))

    async def _redis_listener(self):
        """
        Background task that listens to Redis messages and forwards them 
        to local WebSockets.
        """
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"]
                data = message["data"]
                
                # Route to appropriate local connections
                if channel.startswith("ws:user:"):
                    user_id = channel.split(":")[-1]
                    await self._broadcast_local_user(user_id, data)
                elif channel.startswith("ws:session:"):
                    session_id = channel.split(":")[-1]
                    await self._broadcast_local_session(session_id, data)

    async def _broadcast_local_user(self, user_id: str, data: str):
        if user_id in self.active_connections:
            for ws in list(self.active_connections[user_id]):
                try:
                    await ws.send_text(data)
                except Exception:
                    # Connection likely dead, cleanup handled by disconnect logic usually
                    pass

    async def _broadcast_local_session(self, session_id: str, data: str):
        if session_id in self.session_connections:
            for ws in list(self.session_connections[session_id]):
                try:
                    await ws.send_text(data)
                except Exception:
                    pass

websocket_manager = WebSocketService()