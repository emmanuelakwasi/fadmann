"""
Database setup and session management for SQLite.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Create database directory if it doesn't exist
DB_DIR = "data"
os.makedirs(DB_DIR, exist_ok=True)

# SQLite database URL
DATABASE_URL = f"sqlite:///./{DB_DIR}/fadmann.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL query logging during development
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def init_db():
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (dependency for FastAPI routes)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
