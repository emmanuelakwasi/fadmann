"""
REST API Routes and WebSocket Endpoint

This file contains all the HTTP endpoints (REST API) and the WebSocket endpoint
for real-time chat functionality.

ENDPOINTS PROVIDED:
1. POST /api/auth/login - Login or create user (returns JWT token)
2. GET /api/auth/me - Get current user info (requires JWT)
3. GET /api/rooms - List all rooms
4. POST /api/rooms - Create a new room (requires JWT)
5. GET /api/rooms/{room_id}/messages - Get message history
6. PUT /api/users/{user_id}/profile - Update user profile (requires JWT)
7. GET /api/users/{user_id}/profile - Get user profile
8. WebSocket /api/ws/{room_id} - Real-time chat connection (requires JWT)

AUTHENTICATION:
We use JWT (JSON Web Tokens) for authentication.
- Tokens are signed and self-contained
- Tokens expire after 7 days
- Tokens are validated on every request
- WebSocket connections also require valid JWT tokens

AUTHENTICATION FLOW:
1. User logs in → POST /api/auth/login
2. Server creates JWT token with user info
3. Token returned to frontend
4. Frontend stores token in localStorage
5. Frontend sends token in Authorization header: "Bearer {token}"
6. Server validates token on each request
7. If valid, request proceeds; if invalid, returns 401 Unauthorized
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import hashlib
from typing import List, Optional
from pydantic import BaseModel

from backend.database import get_db, SessionLocal
from backend.models import User, Room, RoomMember, Message
from backend.websocket import manager
from backend.auth import create_access_token, verify_token, get_user_from_token, get_current_user
from backend.validation import validate_username, validate_room_name, validate_message, validate_display_name
from backend.rate_limit import check_rate_limit

# Create router with /api prefix - all routes will be under /api
router = APIRouter(prefix="/api", tags=["api"])


# ============================================================================
# REQUEST/RESPONSE MODELS (Pydantic)
# ============================================================================

class LoginRequest(BaseModel):
    """Request model for login endpoint."""
    username: str
    display_name: str


class RoomCreateRequest(BaseModel):
    """Request model for creating a room."""
    name: str
    description: str = ""
    is_public: bool = True


class UserProfileUpdateRequest(BaseModel):
    """Request model for updating user profile."""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class ReactionRequest(BaseModel):
    """Request model for adding/removing reactions."""
    emoji: str


class ReplyRequest(BaseModel):
    """Request model for replying to a message."""
    content: str
    reply_to: int


# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

# Note: Authentication is now handled by backend.auth module
# The get_current_user function is imported from there
# It validates JWT tokens and returns User objects


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@router.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login or register a user.
    
    This endpoint handles both registration and login:
    - If username doesn't exist, creates a new user
    - If username exists, updates display name if changed
    - Returns a JWT token for subsequent requests
    
    AUTHENTICATION FLOW:
    1. User submits username and display_name
    2. Server validates input (username format, display_name format)
    3. Server checks if user exists (by username)
    4. If new user: creates account in database
    5. If existing user: updates display_name if changed
    6. Server creates JWT token with user info
    7. Token is signed with secret key
    8. Token returned to frontend
    9. Frontend stores token in localStorage
    10. Frontend includes token in all future requests
    
    Args:
        request: LoginRequest with username and display_name
        db: Database session (automatically injected by FastAPI)
    
    Returns:
        Dictionary with:
        - token: JWT token string (store this in localStorage)
        - user: User information (id, username, display_name)
    
    Raises:
        HTTPException 400: If validation fails
    
    Security Notes:
        - Username must be unique and validated
        - Display name is validated
        - No password required (simplified for beginner-friendly app)
        - JWT tokens expire after 7 days
        - Tokens are cryptographically signed (can't be tampered with)
    """
    # Validate username
    is_valid, error = validate_username(request.username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Validate display name
    is_valid, error = validate_display_name(request.display_name)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Try to find existing user by username
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user:
        # User doesn't exist - create new user (registration)
        # Simple password hash (in production, use bcrypt with actual passwords)
        password_hash = hashlib.sha256(request.username.encode()).hexdigest()
        
        user = User(
            username=request.username.strip(),
            email=f"{request.username.strip()}@campus.local",  # Dummy email for now
            password_hash=password_hash,
            display_name=request.display_name.strip()
        )
        db.add(user)
        db.commit()
        db.refresh(user)  # Refresh to get the generated ID
    else:
        # User exists - update display name if it changed
        new_display_name = request.display_name.strip()
        if user.display_name != new_display_name:
            user.display_name = new_display_name
            db.commit()
            db.refresh(user)
    
    # Create JWT token
    # This token contains user_id and username, signed with our secret key
    # Token expires in 7 days
    token = create_access_token(user_id=user.id, username=user.username)
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name
        }
    }


@router.get("/auth/me")
async def get_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's information.
    
    This endpoint requires a valid JWT token in the Authorization header.
    
    HOW IT WORKS:
    1. Frontend sends: Authorization: "Bearer {token}"
    2. get_current_user dependency validates the token
    3. If valid: extracts user_id from token, queries database for user
    4. If invalid: returns 401 Unauthorized
    5. User object is injected into this function
    
    Args:
        user: User object (automatically extracted from JWT token)
        db: Database session (for querying user details)
    
    Returns:
        Dictionary with user information
    
    Raises:
        HTTPException 401: If token is invalid, expired, or missing
    """
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url
    }


# ============================================================================
# ROOM ROUTES
# ============================================================================

@router.get("/rooms")
async def get_rooms(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
) -> List[dict]:
    """
    List all available rooms.
    
    Currently returns all public rooms. In the future, this could:
    - Filter by user's memberships
    - Show private rooms the user has access to
    - Include room metadata (member count, last message, etc.)
    
    Args:
        db: Database session
        user: Optional authenticated user (for future filtering)
    
    Returns:
        List of room dictionaries with id, name, description, is_public
    """
    # Query all public rooms from database
    rooms = db.query(Room).filter(Room.is_public == True).all()
    
    # Convert SQLAlchemy objects to dictionaries
    # This is what FastAPI will serialize to JSON
    return [
        {
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "is_public": room.is_public,
            "created_at": room.created_at.isoformat()
        }
        for room in rooms
    ]


@router.post("/rooms")
async def create_room(
    request: RoomCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Create a new chat room.
    
    Requires authentication. The authenticated user becomes the room creator.
    
    Args:
        request: RoomCreateRequest with name, description, is_public
        db: Database session
        user: Authenticated user (required)
    
    Returns:
        Dictionary with created room information
    
    Raises:
        HTTPException 401: If not authenticated
        HTTPException 400: If validation fails or room name already exists
    """
    # Validate room name
    is_valid, error = validate_room_name(request.name)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Validate description length
    if request.description and len(request.description) > 200:
        raise HTTPException(status_code=400, detail="Description must be no more than 200 characters")
    
    # Check if room name already exists (case-insensitive)
    existing_room = db.query(Room).filter(
        Room.name.ilike(request.name.strip())
    ).first()
    if existing_room:
        raise HTTPException(
            status_code=400, 
            detail=f"Room with name '{request.name}' already exists"
        )
    
    # Create new room
    room = Room(
        name=request.name.strip(),
        description=request.description.strip() if request.description else "",
        is_public=request.is_public,
        created_by=user.id  # Set creator to current user
    )
    
    db.add(room)
    db.commit()
    db.refresh(room)  # Get the generated ID
    
    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "is_public": room.is_public,
        "created_by": user.id,
        "created_at": room.created_at.isoformat()
    }


@router.get("/rooms/{room_id}/messages")
async def get_messages(
    room_id: int, 
    limit: int = Query(100, le=500),  # Max 500 messages
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
) -> List[dict]:
    """
    Get message history for a specific room.
    
    Returns messages in chronological order (oldest first).
    This is used when a user opens a room to see past conversations.
    
    Args:
        room_id: The ID of the room
        limit: Maximum number of messages to return (default 100, max 500)
        db: Database session
    
    Returns:
        List of message dictionaries with full message details
    
    Note:
        Messages are ordered by created_at descending (newest first),
        then reversed to show oldest first (for chat UI)
    """
    # Query messages for this room, ordered by creation time (newest first)
    messages = db.query(Message)\
        .filter(Message.room_id == room_id)\
        .order_by(desc(Message.created_at))\
        .limit(limit)\
        .all()
    
    # Reverse to show oldest first (natural chat order)
    messages.reverse()
    
    # Convert to dictionaries with user information
    result = []
    for msg in messages:
        msg_dict = {
            "id": msg.id,
            "user_id": msg.user_id,
            "username": msg.user.username,
            "display_name": msg.user.display_name,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "message_type": msg.message_type,
            "reactions": msg.reactions if msg.reactions else {},
            "reply_to": msg.reply_to
        }
        
        # If this is a reply, include parent message info
        if msg.reply_to:
            parent = db.query(Message).filter(Message.id == msg.reply_to).first()
            if parent:
                msg_dict["reply_to_message"] = {
                    "id": parent.id,
                    "content": parent.content[:50] + "..." if len(parent.content) > 50 else parent.content,
                    "display_name": parent.user.display_name
                }
        
        result.append(msg_dict)
    
    return result


# ============================================================================
# MESSAGE REACTION ROUTES
# ============================================================================

@router.post("/messages/{message_id}/reactions")
async def toggle_reaction(
    message_id: int,
    request: ReactionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Add or remove an emoji reaction to a message.
    
    If the user already reacted with this emoji, remove it.
    If not, add the reaction.
    
    Args:
        message_id: The ID of the message
        request: ReactionRequest with emoji
        db: Database session
        user: Authenticated user
    
    Returns:
        Updated message with reactions
    """
    # Get the message
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Initialize reactions if None
    if message.reactions is None:
        message.reactions = {}
    
    # Validate emoji (simple check - just ensure it's not empty)
    emoji = request.emoji.strip()
    if not emoji:
        raise HTTPException(status_code=400, detail="Emoji cannot be empty")
    
    # Toggle reaction: if user already reacted, remove; otherwise add
    if emoji not in message.reactions:
        message.reactions[emoji] = []
    
    if user.id in message.reactions[emoji]:
        # Remove reaction
        message.reactions[emoji].remove(user.id)
        # Remove emoji key if no reactions left
        if not message.reactions[emoji]:
            del message.reactions[emoji]
    else:
        # Add reaction
        message.reactions[emoji].append(user.id)
    
    db.commit()
    db.refresh(message)
    
    # Broadcast reaction update via WebSocket
    from backend.websocket import manager
    await manager.broadcast_to_room({
        "type": "reaction_update",
        "message_id": message.id,
        "reactions": message.reactions or {}
    }, message.room_id)
    
    return {
        "message_id": message.id,
        "reactions": message.reactions or {}
    }


# ============================================================================
# USER PROFILE ROUTES
# ============================================================================

@router.get("/users/{user_id}/profile")
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get a user's profile information.
    
    Args:
        user_id: The ID of the user
        db: Database session
    
    Returns:
        Dictionary with user profile information
    
    Raises:
        HTTPException 404: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat()
    }


@router.put("/users/{user_id}/profile")
async def update_user_profile(
    user_id: int,
    request: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a user's profile.
    
    Users can only update their own profile.
    
    Args:
        user_id: The ID of the user to update
        request: UserProfileUpdateRequest with fields to update
        db: Database session
        current_user: Authenticated user (from token)
    
    Returns:
        Updated user profile
    
    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If trying to update another user's profile
        HTTPException 404: If user not found
    """
    # Users can only update their own profile
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You can only update your own profile"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.bio is not None:
        user.bio = request.bio
    if request.avatar_url is not None:
        user.avatar_url = request.avatar_url
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url
    }


# ============================================================================
# WEBSOCKET ENDPOINT (Real-time Chat)
# ============================================================================

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: int, 
    token: str = Query(None)
):
    """
    WebSocket endpoint for real-time chat messaging.
    
    This is the heart of the real-time chat functionality. It:
    1. Validates the user's authentication token
    2. Connects the user to the specified room
    3. Listens for incoming messages
    4. Saves messages to database
    5. Broadcasts messages to all users in the room
    6. Handles typing indicators
    7. Cleans up on disconnect
    
    Connection URL format:
    ws://localhost:8000/api/ws/{room_id}?token={auth_token}
    
    Message format (sent from client):
    {
        "type": "message",
        "content": "Hello everyone!"
    }
    
    Typing format (sent from client):
    {
        "type": "typing",
        "is_typing": true
    }
    
    Args:
        websocket: The WebSocket connection object
        room_id: The ID of the room to join
        token: Authentication token (from query parameter)
    
    What happens:
    1. Validate token and get user
    2. Connect user to room via ConnectionManager
    3. Enter infinite loop listening for messages
    4. Process each message (save to DB, broadcast)
    5. Handle disconnection gracefully
    """
    # ========================================================================
    # STEP 1: AUTHENTICATION (JWT Validation)
    # ========================================================================
    
    # Check if token was provided
    if not token:
        await websocket.close(code=4001, reason="No token provided")
        return
    
    # Validate JWT token
    # verify_token checks:
    # - Token signature is valid (hasn't been tampered with)
    # - Token hasn't expired
    # - Token format is correct
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    # Extract user_id from token payload
    # "sub" (subject) is the standard JWT field for user ID
    user_id = int(payload.get("sub"))
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return
    
    # Get user from database
    # We need a database session to query the user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return
    finally:
        db.close()
    
    # ========================================================================
    # STEP 2: CONNECT TO ROOM
    # ========================================================================
    
    # Connect user to room (this accepts the WebSocket and stores connection)
    await manager.connect(websocket, room_id, user_id)
    
    # ========================================================================
    # STEP 3: MESSAGE LOOP
    # ========================================================================
    
    try:
        # Infinite loop - keeps connection alive and listens for messages
        while True:
            # Wait for incoming message from client
            # This blocks until a message arrives
            data = await websocket.receive_json()
            
            # ================================================================
            # HANDLE MESSAGE TYPE: "message"
            # ================================================================
            if data["type"] == "message":
                # Validate message content
                content = data.get("content", "").strip()
                is_valid, error = validate_message(content)
                if not is_valid:
                    # Send error back to user
                    await websocket.send_json({
                        "type": "error",
                        "message": error
                    })
                    continue
                
                # Check rate limit
                allowed, rate_error = check_rate_limit(user_id)
                if not allowed:
                    # Send rate limit error back to user
                    await websocket.send_json({
                        "type": "error",
                        "message": rate_error
                    })
                    continue
                
                # Create a new database session for this operation
                db_session = SessionLocal()
                try:
                    # Get reply_to if provided
                    reply_to = data.get("reply_to")
                    if reply_to:
                        # Verify the parent message exists and is in the same room
                        parent_msg = db_session.query(Message).filter(
                            Message.id == reply_to,
                            Message.room_id == room_id
                        ).first()
                        if not parent_msg:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Parent message not found"
                            })
                            continue
                    
                    # Create message record in database
                    # Note: created_at is automatically set by the model
                    message = Message(
                        room_id=room_id,
                        user_id=user_id,
                        content=content,  # Use validated, trimmed content
                        message_type=data.get("message_type", "text"),  # Default to "text"
                        reply_to=reply_to if reply_to else None,
                        reactions={}  # Initialize empty reactions
                    )
                    db_session.add(message)
                    db_session.commit()
                    db_session.refresh(message)  # Get the generated ID and timestamp
                    
                    # Get parent message info if this is a reply
                    reply_to_info = None
                    if message.reply_to:
                        parent = db_session.query(Message).filter(Message.id == message.reply_to).first()
                        if parent:
                            reply_to_info = {
                                "id": parent.id,
                                "content": parent.content[:50] + "..." if len(parent.content) > 50 else parent.content,
                                "display_name": parent.user.display_name
                            }
                    
                    # Prepare message data for broadcasting
                    # Use server-side timestamp from database
                    message_data = {
                        "type": "message",
                        "message": {
                            "id": message.id,
                            "user_id": user_id,
                            "username": user.username,
                            "display_name": user.display_name,
                            "content": message.content,
                            "created_at": message.created_at.isoformat(),  # Server-side timestamp
                            "message_type": message.message_type,
                            "reactions": message.reactions or {},
                            "reply_to": message.reply_to,
                            "reply_to_message": reply_to_info
                        }
                    }
                    
                    # Broadcast to ALL users in room (including sender)
                    # This is what makes the chat real-time - everyone sees it instantly
                    await manager.broadcast_to_room(message_data, room_id)
                finally:
                    # Always close database session
                    db_session.close()
            
            # ================================================================
            # HANDLE MESSAGE TYPE: "typing"
            # ================================================================
            elif data["type"] == "typing":
                # Handle typing indicator
                # Frontend sends this when user starts/stops typing
                await manager.handle_typing(
                    room_id, 
                    user_id, 
                    data.get("is_typing", False), 
                    user.username
                )
            
            # ================================================================
            # HANDLE MESSAGE TYPE: "reaction"
            # ================================================================
            elif data["type"] == "reaction":
                # Handle emoji reaction via WebSocket (alternative to REST endpoint)
                message_id = data.get("message_id")
                emoji = data.get("emoji", "").strip()
                
                if not message_id or not emoji:
                    await websocket.send_json({
                        "type": "error",
                        "message": "message_id and emoji required"
                    })
                    continue
                
                # Get message and verify it's in the current room
                db_session = SessionLocal()
                try:
                    message = db_session.query(Message).filter(
                        Message.id == message_id,
                        Message.room_id == room_id
                    ).first()
                    
                    if not message:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Message not found"
                        })
                        continue
                    
                    # Initialize reactions if None
                    if message.reactions is None:
                        message.reactions = {}
                    
                    # Toggle reaction
                    if emoji not in message.reactions:
                        message.reactions[emoji] = []
                    
                    if user_id in message.reactions[emoji]:
                        # Remove reaction
                        message.reactions[emoji].remove(user_id)
                        if not message.reactions[emoji]:
                            del message.reactions[emoji]
                    else:
                        # Add reaction
                        message.reactions[emoji].append(user_id)
                    
                    db_session.commit()
                    db_session.refresh(message)
                    
                    # Broadcast reaction update
                    await manager.broadcast_to_room({
                        "type": "reaction_update",
                        "message_id": message.id,
                        "reactions": message.reactions or {}
                    }, room_id)
                finally:
                    db_session.close()
    
    # ========================================================================
    # STEP 4: CLEANUP ON DISCONNECT
    # ========================================================================
    
    except WebSocketDisconnect:
        # User closed the connection (closed browser, navigated away, etc.)
        # This is normal - user intentionally disconnected
        manager.disconnect(room_id, user_id)
        # Notify others that user left
        await manager.broadcast_user_event(room_id, user_id, "user_left")
    
    except Exception as e:
        # Handle any other errors gracefully
        print(f"WebSocket error: {e}")
        try:
            manager.disconnect(room_id, user_id)
            await manager.broadcast_user_event(room_id, user_id, "user_left")
        except Exception:
            pass  # Ignore errors during cleanup
