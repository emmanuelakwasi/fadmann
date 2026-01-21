"""
FastAPI main application file.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import init_db
from app.routes import router

# Initialize FastAPI app
app = FastAPI(
    title="FadMann",
    description="Campus chat app for students to reconnect",
    version="0.1.0"
)

# Add CORS middleware (needed for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on app startup."""
    init_db()
    
    # Create default public rooms if they don't exist
    from app.database import SessionLocal
    from app.models import Room, User
    
    db = SessionLocal()
    try:
        # Check if default rooms exist
        general_room = db.query(Room).filter(Room.name == "General").first()
        if not general_room:
            # Create a default admin user if none exists
            admin = db.query(User).first()
            if not admin:
                admin = User(
                    username="system",
                    email="system@fadmann.local",
                    password_hash="",
                    display_name="System"
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
            
            # Create default rooms
            rooms = [
                Room(name="General", description="General campus chat", is_public=True, created_by=admin.id),
                Room(name="Study Groups", description="Find study partners", is_public=True, created_by=admin.id),
                Room(name="Campus Events", description="Campus events and activities", is_public=True, created_by=admin.id),
            ]
            for room in rooms:
                db.add(room)
            db.commit()
            print("✓ Default rooms created")
        else:
            print("✓ Database initialized")
    finally:
        db.close()


# Mount static files (HTML, CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    html_path = os.path.join(static_dir, "index.html")
    return FileResponse(html_path)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "FadMann is running"}
