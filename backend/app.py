"""
FastAPI Main Application Entry Point

Author: Emmanuel Akwasi Opoku
GitHub: https://github.com/emmanuelakwasi
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from backend.database import init_db
from backend.routes import router

app = FastAPI(
    title="FadMann",
    description="Campus chat app for students to reconnect",
    version="0.1.0"
)

cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins != "*":
    cors_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    init_db()
    
    from backend.database import SessionLocal
    from backend.models import Room, User
    
    db = SessionLocal()
    try:
        general_room = db.query(Room).filter(Room.name == "General").first()
        
        if not general_room:
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
            
            rooms = [
                Room(name="General", description="General campus chat", is_public=True, created_by=admin.id),
                Room(name="Study Groups", description="Find study partners", is_public=True, created_by=admin.id),
                Room(name="Campus Events", description="Campus events and activities", is_public=True, created_by=admin.id),
            ]
            
            for room in rooms:
                db.add(room)
            db.commit()
            print("Default rooms created")
        else:
            print("Database initialized")
    finally:
        db.close()


frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def read_root():
    html_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "Frontend files not found. Please check frontend/ directory."}

@app.get("/health")
async def health_check():
    from backend.database import engine
    from datetime import datetime
    
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
