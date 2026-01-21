"""
Database Configuration and Session Management

This file sets up SQLite database connection using SQLAlchemy ORM.
SQLAlchemy is an Object-Relational Mapping library that lets us work with
databases using Python objects instead of writing raw SQL.

WHY SQLITE?
- Perfect for beginners: No separate database server needed
- File-based: Database is just a file (data/fadmann.db)
- Works out of the box: No installation or configuration
- Great for development and small deployments
- Can easily migrate to PostgreSQL later if needed

WHY SQLALCHEMY?
- Easy to use: Define models as Python classes
- Type-safe: Catches errors at development time
- Database-agnostic: Can switch databases easily
- Built-in migrations: Can update schema easily
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DB_DIR = os.getenv("DATABASE_PATH", "data")
try:
    os.makedirs(DB_DIR, exist_ok=True)
except (OSError, PermissionError):
    DB_DIR = "/tmp/data"
    os.makedirs(DB_DIR, exist_ok=True)

# SQLite database URL
# Format: sqlite:///./path/to/database.db
# The "./" means relative to current directory
DATABASE_URL = f"sqlite:///./{DB_DIR}/fadmann.db"

# ============================================================================
# SQLALCHEMY ENGINE
# ============================================================================

# Create database engine
# The engine manages the connection pool and executes SQL
engine = create_engine(
    DATABASE_URL,
    # SQLite-specific: Allow multiple threads to use same connection
    # (SQLite normally doesn't allow this, but we need it for FastAPI)
    connect_args={"check_same_thread": False},
    # Set to True to see all SQL queries in console (useful for debugging)
    echo=False
)

# ============================================================================
# SESSION FACTORY
# ============================================================================

# Create session factory
# A session is like a "transaction" - it groups database operations together
# autocommit=False: We manually commit changes (more control)
# autoflush=False: We manually flush changes (more control)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================================
# BASE CLASS FOR MODELS
# ============================================================================

# Base class that all our models will inherit from
# This gives them database table functionality
Base = declarative_base()

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def init_db():
    """
    Initialize database by creating all tables.
    
    This function reads all models that inherit from Base and creates
    the corresponding tables in the database.
    
    Call this once when the app starts (see app.py startup event).
    """
    # Create all tables defined in models.py
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Get a database session (dependency for FastAPI routes).
    
    This is a "dependency" function that FastAPI will call automatically
    when a route needs database access. It:
    1. Creates a new database session
    2. Yields it to the route function
    3. Closes it when the route finishes (even if there's an error)
    
    Usage in routes:
        @router.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            # Use db here to query database
            users = db.query(User).all()
            return users
        # db is automatically closed here
    
    This pattern ensures we never forget to close database connections.
    """
    db = SessionLocal()
    try:
        # Yield gives the session to the route, then continues here after
        yield db
    finally:
        # Always close the session, even if an error occurred
        db.close()
