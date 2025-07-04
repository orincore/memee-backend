#!/usr/bin/env python3
"""
Startup script for Render.com deployment
This script ensures the FastAPI app binds to the correct port
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Get port from environment variable (Render.com sets this)
    port = int(os.getenv("PORT", 8000))
    
    # Get host - bind to 0.0.0.0 for external access
    host = "0.0.0.0"
    
    print(f"Starting Memee API on {host}:{port}")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    ) 