#!/usr/bin/env python3
"""
Simple script to run FadMann locally with one command.
Works on Windows, macOS, and Linux.
"""
import uvicorn
import os

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Run the FastAPI app
    print("🚀 Starting FadMann...")
    print("📱 Open http://localhost:8000 in your browser")
    print("💡 Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )
