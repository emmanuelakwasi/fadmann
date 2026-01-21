"""
Database Models (SQLAlchemy ORM)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(String(255), default="")
    bio = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    room_memberships = relationship("RoomMember", back_populates="user", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, default="")
    is_public = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")
    members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")


class RoomMember(Base):
    __tablename__ = "room_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)

    user = relationship("User", back_populates="room_memberships")
    room = relationship("Room", back_populates="members")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    file_url = Column(String(255), default="")
    reactions = Column(JSON, default=dict)
    reply_to = Column(Integer, ForeignKey("messages.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")
    parent_message = relationship("Message", remote_side=[id], backref="replies")


class TypingIndicator(Base):
    __tablename__ = "typing_indicators"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_typing = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
