"""
API routes for authentication, rooms, and messages.
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import hashlib
import secrets
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db, SessionLocal
from app.models import User, Room, RoomMember, Message
from app.websocket import manager

router = APIRouter(prefix="/api", tags=["api"])

# Simple token storage (in production, use proper JWT or session management)
# Format: {token: user_id}
auth_tokens = {}

# Format: {user_id: user_object}
active_users = {}


class LoginRequest(BaseModel):
    username: str
    display_name: str


def get_current_user_from_token(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Get current user from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "").strip()
    user_id = auth_tokens.get(token)
    if user_id:
        return active_users.get(user_id)
    return None


# Authentication routes
@router.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login or register a user."""
    # Simple auth: find or create user
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user:
        # Create new user
        # Simple password hash (in production, use proper hashing like bcrypt)
        password_hash = hashlib.sha256(request.username.encode()).hexdigest()
        
        user = User(
            username=request.username,
            email=f"{request.username}@campus.local",  # Dummy email
            password_hash=password_hash,
            display_name=request.display_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update display name if changed
        if user.display_name != request.display_name:
            user.display_name = request.display_name
            db.commit()
            db.refresh(user)
    
    # Generate token
    token = secrets.token_urlsafe(32)
    auth_tokens[token] = user.id
    active_users[user.id] = user
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name
        }
    }


@router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user_from_token)):
    """Get current user info."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name
    }


# Room routes
@router.get("/rooms")
async def get_rooms(db: Session = Depends(get_db)) -> List[dict]:
    """Get all public rooms and rooms the user is a member of."""
    # For now, return all public rooms
    rooms = db.query(Room).filter(Room.is_public == True).all()
    
    return [
        {
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "is_public": room.is_public
        }
        for room in rooms
    ]


@router.get("/rooms/{room_id}/messages")
async def get_messages(room_id: int, limit: int = 100, db: Session = Depends(get_db)) -> List[dict]:
    """Get message history for a room."""
    messages = db.query(Message).filter(Message.room_id == room_id)\
        .order_by(desc(Message.created_at))\
        .limit(limit)\
        .all()
    
    # Reverse to show oldest first
    messages.reverse()
    
    return [
        {
            "id": msg.id,
            "user_id": msg.user_id,
            "username": msg.user.username,
            "display_name": msg.user.display_name,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "message_type": msg.message_type
        }
        for msg in messages
    ]


# WebSocket endpoint
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str = None):
    """WebSocket endpoint for real-time messaging."""
    # Validate token and get user
    if not token:
        await websocket.close(code=4001, reason="No token provided")
        return
    
    user_id = auth_tokens.get(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user = active_users.get(user_id)
    if not user:
        await websocket.close(code=4001, reason="User not found")
        return
    
    # Connect to room
    await manager.connect(websocket, room_id, user_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                # Save message to database
                db = SessionLocal()
                try:
                    message = Message(
                        room_id=room_id,
                        user_id=user_id,
                        content=data["content"],
                        message_type=data.get("message_type", "text")
                    )
                    db.add(message)
                    db.commit()
                    db.refresh(message)
                    
                    # Broadcast to room (including sender)
                    message_data = {
                        "type": "message",
                        "message": {
                            "id": message.id,
                            "user_id": user_id,
                            "username": user.username,
                            "display_name": user.display_name,
                            "content": message.content,
                            "created_at": message.created_at.isoformat(),
                            "message_type": message.message_type
                        }
                    }
                    # Send to all users in room
                    await manager.broadcast_to_room(message_data, room_id)
                finally:
                    db.close()
            
            elif data["type"] == "typing":
                # Handle typing indicator
                await manager.handle_typing(room_id, user_id, data.get("is_typing", False), user.username)
    
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(room_id, user_id)
