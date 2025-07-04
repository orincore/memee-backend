import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Reduce verbose logging from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("cloudinary").setLevel(logging.WARNING)

from app.routes import memes, products, fetch_memes, auth, friends, scheduler
from app.services.async_scheduler_service import async_meme_scheduler

app = FastAPI(title="Memee Meme Aggregator API")

# CORS configuration
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(memes.router)
app.include_router(products.router)
app.include_router(fetch_memes.router)
app.include_router(auth.router)
app.include_router(friends.router)
app.include_router(scheduler.router)

@app.on_event("startup")
async def startup_event():
    """Start the meme scheduler when the app starts"""
    try:
        async_meme_scheduler.start()
        logging.info("Async meme scheduler started successfully")
    except Exception as e:
        logging.error(f"Failed to start async meme scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the meme scheduler when the app shuts down"""
    try:
        async_meme_scheduler.stop()
        logging.info("Async meme scheduler stopped successfully")
    except Exception as e:
        logging.error(f"Failed to stop async meme scheduler: {e}") 