"""
WebSocket Connection Manager - In-Memory Connection Tracking

This module manages all active WebSocket connections in memory.
It tracks which users are connected to which rooms and handles
real-time message broadcasting.

WHY IN-MEMORY?
- Fast: No database queries needed for real-time operations
- Simple: Perfect for beginner-friendly implementation
- Scalable enough for small to medium deployments
- For production at scale, consider Redis for distributed systems

Data Structures:
- active_connections: {room_id: {user_id: websocket}}
  Stores the actual WebSocket connections organized by room and user
- typing_users: {room_id: {user_id: timestamp}}
  Tracks who is currently typing in each room
"""
from fastapi import WebSocket
from typing import Dict, Set
from datetime import datetime

# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

# Store active WebSocket connections
# Structure: {room_id: {user_id: websocket}}
# Example: {1: {5: <WebSocket>, 7: <WebSocket>}, 2: {5: <WebSocket>}}
# This means room 1 has users 5 and 7, room 2 has user 5
active_connections: Dict[int, Dict[int, WebSocket]] = {}

# Store typing indicators (who is currently typing)
# Structure: {room_id: {user_id: timestamp}}
# We track timestamps to auto-clear stale typing indicators
typing_users: Dict[int, Dict[int, datetime]] = {}


# ============================================================================
# CONNECTION MANAGER CLASS
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections for real-time chat.
    
    This class handles:
    - Connecting users to rooms
    - Disconnecting users from rooms
    - Broadcasting messages to all users in a room
    - Managing typing indicators
    - Cleaning up dead connections
    """
    
    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        """
        Connect a user to a room via WebSocket.
        
        Args:
            websocket: The WebSocket connection object
            room_id: The ID of the room to join
            user_id: The ID of the user joining
        
        What happens:
        1. Accept the WebSocket connection (handshake)
        2. If user was already connected, close old connection first
        3. Add the connection to our in-memory store
        4. Notify other users in the room that someone joined
        
        RECONNECTION HANDLING:
        - If user reconnects, old connection is replaced
        - This prevents duplicate connections
        - Ensures only one active connection per user per room
        """
        # If user was already connected to this room, close old connection first
        # This handles reconnection gracefully
        if room_id in active_connections and user_id in active_connections[room_id]:
            try:
                old_websocket = active_connections[room_id][user_id]
                await old_websocket.close(code=1000, reason="Reconnecting")
            except Exception:
                pass  # Old connection might already be closed
            # Remove old connection
            del active_connections[room_id][user_id]
        
        # Accept the WebSocket connection (completes the handshake)
        await websocket.accept()
        
        # Initialize room dictionary if it doesn't exist
        if room_id not in active_connections:
            active_connections[room_id] = {}
        
        # Store this user's connection for this room
        active_connections[room_id][user_id] = websocket
        
        # Notify other users in the room that someone joined
        # (We exclude the joiner so they don't see their own join message)
        await self.broadcast_user_event(room_id, user_id, "user_joined")
    
    def disconnect(self, room_id: int, user_id: int):
        """
        Disconnect a user from a room.
        
        Args:
            room_id: The room ID
            user_id: The user ID to disconnect
        
        What happens:
        1. Remove the connection from our store
        2. Clean up empty rooms to save memory
        """
        # Check if room and user exist in our connections
        if room_id in active_connections and user_id in active_connections[room_id]:
            # Remove this user's connection
            del active_connections[room_id][user_id]
            
            # If the room is now empty, remove it to save memory
            if not active_connections[room_id]:
                del active_connections[room_id]
    
    async def send_personal_message(self, message: dict, room_id: int, user_id: int):
        """
        Send a message to a specific user in a room.
        
        Args:
            message: Dictionary containing message data
            room_id: The room ID
            user_id: The target user ID
        
        Use case: Sending private notifications or acknowledgments
        """
        # Check if user is connected to this room
        if room_id in active_connections and user_id in active_connections[room_id]:
            websocket = active_connections[room_id][user_id]
            await websocket.send_json(message)
    
    async def broadcast_to_room(
        self, 
        message: dict, 
        room_id: int, 
        exclude_user_id: int = None
    ):
        """
        Broadcast a message to ALL users in a room.
        
        Args:
            message: Dictionary containing message data (must be JSON-serializable)
            room_id: The room to broadcast to
            exclude_user_id: Optional user ID to exclude from broadcast
                            (useful when sender shouldn't see their own message)
        
        What happens:
        1. Loop through all connected users in the room
        2. Send the message to each user's WebSocket
        3. Handle dead connections gracefully (remove them)
        
        This is the core function for real-time chat - every message
        goes through this function to reach all users in a room.
        """
        # If room doesn't exist or has no connections, nothing to do
        if room_id not in active_connections:
            return
        
        # Track which connections died so we can clean them up
        disconnected = []
        
        # Loop through all users connected to this room
        for user_id, websocket in active_connections[room_id].items():
            # Skip excluded user (usually the sender)
            if user_id == exclude_user_id:
                continue
            
            try:
                # Send the message as JSON
                await websocket.send_json(message)
            except Exception:
                # Connection is dead (user closed browser, network issue, etc.)
                # Mark for removal instead of crashing
                disconnected.append(user_id)
        
        # Clean up dead connections
        for user_id in disconnected:
            self.disconnect(room_id, user_id)
    
    async def broadcast_user_event(self, room_id: int, user_id: int, event_type: str):
        """
        Broadcast a user event (join/leave) to a room.
        
        Args:
            room_id: The room ID
            user_id: The user who triggered the event
            event_type: Type of event ("user_joined" or "user_left")
        
        Use case: Notifying room when users join or leave
        """
        message = {
            "type": event_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Broadcast to everyone except the user who triggered it
        await self.broadcast_to_room(message, room_id, exclude_user_id=user_id)
    
    async def handle_typing(
        self, 
        room_id: int, 
        user_id: int, 
        is_typing: bool, 
        username: str = None
    ):
        """
        Handle typing indicator updates.
        
        Args:
            room_id: The room ID
            user_id: The user who is typing
            is_typing: True if user started typing, False if stopped
            username: Optional username to display
        
        What happens:
        1. Update our typing_users dictionary
        2. Broadcast typing status to all other users in the room
        3. Frontend shows "User is typing..." message
        """
        # Update typing status
        if is_typing:
            # User started typing - add to tracking
            if room_id not in typing_users:
                typing_users[room_id] = {}
            typing_users[room_id][user_id] = datetime.utcnow()
        else:
            # User stopped typing - remove from tracking
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
    
    def get_room_users(self, room_id: int) -> Set[int]:
        """
        Get list of user IDs currently connected to a room.
        
        Args:
            room_id: The room ID
        
        Returns:
            Set of user IDs connected to the room
        
        Use case: Showing "X users online" in room info
        """
        if room_id not in active_connections:
            return set()
        return set(active_connections[room_id].keys())


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Create a single global instance that all routes will use
# This ensures we have one source of truth for all connections
manager = ConnectionManager()
