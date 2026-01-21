"""
Database Models (SQLAlchemy ORM)

This file defines all the database tables as Python classes.
Each class represents a table, and each attribute represents a column.

WHY MODELS?
- Type safety: Python knows what data types to expect
- Relationships: Easy to link tables together
- Validation: SQLAlchemy validates data before saving
- Migrations: Can update schema easily

TABLES DEFINED:
1. User - Stores user accounts and profiles
2. Room - Stores chat rooms (public and private)
3. RoomMember - Links users to rooms (many-to-many relationship)
4. Message - Stores all chat messages
5. TypingIndicator - (Optional) Could store typing status in DB
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class User(Base):
    """
    User Model - Stores user accounts and profiles.
    
    This table stores all user information including:
    - Authentication data (username, password hash)
    - Profile information (display name, bio, avatar)
    - Timestamps (when account was created)
    
    Relationships:
    - Has many Messages (one user can send many messages)
    - Has many RoomMemberships (one user can be in many rooms)
    """
    __tablename__ = "users"  # Table name in database

    # Primary key - unique identifier for each user
    id = Column(Integer, primary_key=True, index=True)
    
    # Username must be unique and indexed for fast lookups
    username = Column(String(50), unique=True, index=True, nullable=False)
    
    # Email must be unique (for future email verification)
    email = Column(String(100), unique=True, index=True, nullable=False)
    
    # Password hash (never store plain passwords!)
    password_hash = Column(String(255), nullable=False)
    
    # Display name shown in chat
    display_name = Column(String(100), nullable=False)
    
    # Avatar URL (for future profile pictures)
    avatar_url = Column(String(255), default="")
    
    # User bio/status message
    bio = Column(Text, default="")
    
    # When the account was created
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships - these let us easily access related data
    # Example: user.messages gives all messages sent by this user
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    room_memberships = relationship("RoomMember", back_populates="user", cascade="all, delete-orphan")


class Room(Base):
    """
    Room Model - Stores chat rooms (public and private).
    
    Rooms are where conversations happen. They can be:
    - Public: Anyone can join (like "General" chat)
    - Private: Only invited members can join (future feature)
    
    Relationships:
    - Has many Messages (one room has many messages)
    - Has many RoomMembers (one room has many members)
    - Belongs to User (created_by references a user)
    """
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    
    # Room name (e.g., "General", "Study Group 1")
    name = Column(String(100), nullable=False, index=True)
    
    # Room description (shown in room list)
    description = Column(Text, default="")
    
    # True = public room (anyone can join)
    # False = private room (only members can join)
    is_public = Column(Boolean, default=True)
    
    # Foreign key to users table - who created this room
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # When the room was created
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")
    members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")


class RoomMember(Base):
    """
    RoomMember Model - Links users to rooms (many-to-many relationship).
    
    This is a "junction table" that connects Users and Rooms.
    Why needed? Because:
    - One user can be in many rooms
    - One room can have many users
    - This is a "many-to-many" relationship
    
    This table stores:
    - Which users are in which rooms
    - When they joined
    - Whether they're an admin
    
    Example data:
    user_id=5, room_id=1  → User 5 is in Room 1
    user_id=5, room_id=2  → User 5 is also in Room 2
    user_id=7, room_id=1  → User 7 is also in Room 1
    """
    __tablename__ = "room_members"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to users table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Foreign key to rooms table
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    
    # When the user joined this room
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Whether this user is an admin of the room (can delete messages, etc.)
    is_admin = Column(Boolean, default=False)

    # Relationships - access the user or room from a RoomMember
    user = relationship("User", back_populates="room_memberships")
    room = relationship("Room", back_populates="members")


class Message(Base):
    """
    Message Model - Stores all chat messages.
    
    Every message sent in any room is stored here.
    This gives us message history - users can see past conversations.
    
    Relationships:
    - Belongs to User (user_id - who sent it)
    - Belongs to Room (room_id - which room it's in)
    
    Message types:
    - "text": Regular text message
    - "file": File attachment (future feature)
    - "voice": Voice message (future feature)
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to rooms table - which room this message is in
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    
    # Foreign key to users table - who sent this message
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # The actual message content
    content = Column(Text, nullable=False)
    
    # Type of message: "text", "file", "voice" (for future features)
    message_type = Column(String(20), default="text")
    
    # URL to file/voice message (for future file sharing feature)
    file_url = Column(String(255), default="")
    
    # Emoji reactions - stored as JSON: {"👍": [user_id1, user_id2], "❤️": [user_id3]}
    # Each emoji maps to a list of user IDs who reacted with that emoji
    reactions = Column(JSON, default=dict)
    
    # Reply to another message (nullable - if null, this is a top-level message)
    reply_to = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    # When the message was sent (indexed for fast sorting)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships - access the user or room from a message
    user = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")
    # Self-referential relationship for replies
    parent_message = relationship("Message", remote_side=[id], backref="replies")


class TypingIndicator(Base):
    """Model to track typing indicators (optional, can use in-memory for real-time)."""
    __tablename__ = "typing_indicators"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_typing = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
