"""
WebSocket handlers for real-time messaging and typing indicators.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from datetime import datetime

# Store active WebSocket connections
# Format: {room_id: {user_id: websocket}}
active_connections: Dict[int, Dict[int, WebSocket]] = {}

# Store typing indicators
# Format: {room_id: {user_id: timestamp}}
typing_users: Dict[int, Dict[int, datetime]] = {}


class ConnectionManager:
    """Manages WebSocket connections per room."""
    
    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        """Add a new WebSocket connection for a user in a room."""
        await websocket.accept()
        
        if room_id not in active_connections:
            active_connections[room_id] = {}
        
        active_connections[room_id][user_id] = websocket
        
        # Notify others in the room that user joined
        await self.broadcast_user_event(room_id, user_id, "user_joined")
    
    def disconnect(self, room_id: int, user_id: int):
        """Remove a WebSocket connection."""
        if room_id in active_connections and user_id in active_connections[room_id]:
            del active_connections[room_id][user_id]
            
            # Clean up empty rooms
            if not active_connections[room_id]:
                del active_connections[room_id]
    
    async def send_personal_message(self, message: dict, room_id: int, user_id: int):
        """Send a message to a specific user in a room."""
        if room_id in active_connections and user_id in active_connections[room_id]:
            websocket = active_connections[room_id][user_id]
            await websocket.send_json(message)
    
    async def broadcast_to_room(self, message: dict, room_id: int, exclude_user_id: int = None):
        """Broadcast a message to all users in a room."""
        if room_id not in active_connections:
            return
        
        disconnected = []
        for user_id, websocket in active_connections[room_id].items():
            if user_id == exclude_user_id:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception:
                # Connection is dead, mark for removal
                disconnected.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected:
            self.disconnect(room_id, user_id)
    
    async def broadcast_user_event(self, room_id: int, user_id: int, event_type: str):
        """Broadcast user join/leave events."""
        message = {
            "type": event_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_room(message, room_id, exclude_user_id=user_id)
    
    async def handle_typing(self, room_id: int, user_id: int, is_typing: bool, username: str = None):
        """Handle typing indicator updates."""
        if is_typing:
            if room_id not in typing_users:
                typing_users[room_id] = {}
            typing_users[room_id][user_id] = datetime.utcnow()
        else:
            if room_id in typing_users and user_id in typing_users[room_id]:
                del typing_users[room_id][user_id]
        
        # Broadcast typing status to room (except to the typer)
        message = {
            "type": "typing",
            "user_id": user_id,
            "username": username or f"User{user_id}",
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_room(message, room_id, exclude_user_id=user_id)


# Global connection manager instance
manager = ConnectionManager()
