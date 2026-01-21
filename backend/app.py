"""
FastAPI Main Application Entry Point

This is the main file that creates and configures the FastAPI application.
It's the entry point that ties everything together:
- Database initialization
- Route registration
- Static file serving
- CORS configuration
- Startup/shutdown events

When you run the app (python run.py), this file is loaded and
the FastAPI app starts listening for HTTP requests.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.database import init_db
from backend.routes import router

# ============================================================================
# CREATE FASTAPI APPLICATION
# ============================================================================

# Initialize FastAPI app
# This creates the main application object
app = FastAPI(
    title="FadMann",
    description="Campus chat app for students to reconnect",
    version="0.1.0"
)

# ============================================================================
# CORS MIDDLEWARE (Cross-Origin Resource Sharing)
# ============================================================================

# CORS allows the frontend (running on different port) to make requests
# to the backend API. Without this, browsers block cross-origin requests.
# Get CORS origins from environment variable, default to "*" for development
cors_origins = os.getenv("CORS_ORIGINS", "*")
# If multiple origins are provided, split by comma
if cors_origins != "*":
    cors_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Use environment variable in production
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# REGISTER ROUTES
# ============================================================================

# Include all API routes from routes.py
# This makes all endpoints in routes.py available
app.include_router(router)

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Run when the application starts.
    
    This function is called automatically by FastAPI when the server starts.
    We use it to:
    1. Initialize the database (create tables if they don't exist)
    2. Create default rooms for users to chat in
    
    This ensures the database is ready before handling any requests.
    """
    # Initialize database - creates all tables defined in models.py
    init_db()
    
    # Import here to avoid circular dependencies
    from backend.database import SessionLocal
    from backend.models import Room, User
    
    # Create database session
    db = SessionLocal()
    try:
        # Check if default rooms already exist
        general_room = db.query(Room).filter(Room.name == "General").first()
        
        if not general_room:
            # No rooms exist yet - create default setup
            
            # First, create a system user to be the creator of default rooms
            admin = db.query(User).first()
            if not admin:
                admin = User(
                    username="system",
                    email="system@fadmann.local",
                    password_hash="",  # System user doesn't need password
                    display_name="System"
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
            
            # Create default public rooms
            rooms = [
                Room(
                    name="General", 
                    description="General campus chat", 
                    is_public=True, 
                    created_by=admin.id
                ),
                Room(
                    name="Study Groups", 
                    description="Find study partners", 
                    is_public=True, 
                    created_by=admin.id
                ),
                Room(
                    name="Campus Events", 
                    description="Campus events and activities", 
                    is_public=True, 
                    created_by=admin.id
                ),
            ]
            
            # Add all rooms to database
            for room in rooms:
                db.add(room)
            db.commit()
            print("✓ Default rooms created")
        else:
            print("✓ Database initialized")
    finally:
        # Always close database session
        db.close()


# ============================================================================
# STATIC FILES (Frontend)
# ============================================================================

# Mount the frontend directory to serve static files (HTML, CSS, JS)
# Files in frontend/ will be accessible at /static/
# Example: frontend/css/style.css → http://localhost:8000/static/css/style.css
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# ============================================================================
# ROOT ROUTES
# ============================================================================

@app.get("/")
async def read_root():
    """
    Serve the main HTML page.
    
    When users visit http://localhost:8000/, they get the chat interface.
    """
    html_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "Frontend files not found. Please check frontend/ directory."}


@app.get("/health")
async def health_check():
    """
    Health check endpoint for deployment monitoring.
    
    Deployment platforms (like Render, Heroku, etc.) use this to check
    if the server is running and healthy. Returns status and basic info.
    
    Returns:
        Dictionary with:
        - status: "ok" if healthy
        - message: Status message
        - timestamp: Current server time
        - database: Database connection status
    """
    from backend.database import engine
    from datetime import datetime
    
    # Check database connection
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "message": "FadMann is running",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status
    }
