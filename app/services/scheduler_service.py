import os
import time
import random
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.reddit_service import fetch_and_store_memes
from app.services.instagram_service import fetch_and_store_instagram_memes_batch
from app.meme_subreddits import MEME_SUBREDDITS
from app.config.scheduler_config import (
    SCHEDULER_ENABLED, REDDIT_FETCH_INTERVAL_MINUTES, INSTAGRAM_FETCH_INTERVAL_MINUTES,
    REDDIT_CATEGORIES, REDDIT_CATEGORIES_PER_CYCLE, REDDIT_FETCH_DELAY_SECONDS,
    SCHEDULER_LOG_LEVEL
)
import logging

# Set up logging
logging.basicConfig(level=getattr(logging, SCHEDULER_LOG_LEVEL))

# Reduce verbose logging from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("cloudinary").setLevel(logging.WARNING)
logging.getLogger("praw").setLevel(logging.WARNING)
logging.getLogger("instagrapi").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Thread pool for running fetch operations
fetch_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="meme_fetch")

class MemeScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
    def start(self):
        """Start the scheduler"""
        if not self.is_running and SCHEDULER_ENABLED:
            # Schedule Reddit meme fetching
            self.scheduler.add_job(
                func=self.fetch_reddit_memes_job,
                trigger=IntervalTrigger(minutes=REDDIT_FETCH_INTERVAL_MINUTES),
                id='reddit_meme_fetch',
                name='Fetch Reddit Memes',
                replace_existing=True
            )
            
            # Schedule Instagram meme fetching (offset by 5 minutes to avoid conflicts)
            self.scheduler.add_job(
                func=self.fetch_instagram_memes_job,
                trigger=IntervalTrigger(minutes=INSTAGRAM_FETCH_INTERVAL_MINUTES),
                id='instagram_meme_fetch',
                name='Fetch Instagram Memes',
                replace_existing=True,
                next_run_time=datetime.now().replace(second=0, microsecond=0).replace(minute=datetime.now().minute + 5)
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Meme scheduler started successfully - Reddit: {REDDIT_FETCH_INTERVAL_MINUTES}min, Instagram: {INSTAGRAM_FETCH_INTERVAL_MINUTES}min")
            
            # Run initial fetch in background (non-blocking)
            logger.info("Starting initial background fetches...")
            self.fetch_reddit_memes_job()
            self.fetch_instagram_memes_job()
        elif not SCHEDULER_ENABLED:
            logger.info("Scheduler is disabled in configuration")
        else:
            logger.info("Scheduler is already running")
    

    
    def fetch_reddit_memes_job(self):
        """Job to fetch Reddit memes - runs in separate thread to avoid blocking"""
        try:
            logger.info(f"[Reddit Scheduler] Starting Reddit meme fetch at {datetime.now()}")
            
            # Submit the fetch task to thread pool to avoid blocking the main thread
            future = fetch_executor.submit(self._fetch_reddit_memes_worker)
            
            # Add callback to log completion
            def log_completion(fut):
                try:
                    fut.result()  # This will raise any exception that occurred
                    logger.info(f"[Reddit Scheduler] Reddit meme fetch completed successfully at {datetime.now()}")
                except Exception as e:
                    logger.error(f"[Reddit Scheduler] Reddit meme fetch failed: {e}")
            
            future.add_done_callback(log_completion)
            
        except Exception as e:
            logger.error(f"[Reddit Scheduler] Critical error in Reddit fetch job: {e}")
    
    def _fetch_reddit_memes_worker(self):
        """Worker function that runs in separate thread to fetch Reddit memes"""
        try:
            # Randomly select categories to fetch from
            selected_categories = random.sample(REDDIT_CATEGORIES, min(REDDIT_CATEGORIES_PER_CYCLE, len(REDDIT_CATEGORIES)))
            
            total_inserted = 0
            
            for category in selected_categories:
                try:
                    logger.info(f"[Reddit Scheduler] Fetching memes for category: {category}")
                    
                    # Randomly select a subreddit for this category
                    subreddit = random.choice(MEME_SUBREDDITS)
                    
                    # Fetch and store memes
                    fetch_and_store_memes(category, subreddit)
                    
                    logger.info(f"[Reddit Scheduler] Completed fetch for category: {category}, subreddit: {subreddit}")
                    
                    # Add a small delay between categories to avoid rate limiting
                    time.sleep(REDDIT_FETCH_DELAY_SECONDS)
                    
                except Exception as e:
                    logger.error(f"[Reddit Scheduler] Error fetching for category {category}: {e}")
                    continue
            
            logger.info(f"[Reddit Scheduler] Reddit meme fetch worker completed at {datetime.now()}")
            
        except Exception as e:
            logger.error(f"[Reddit Scheduler] Critical error in Reddit fetch worker: {e}")
            raise
    
    def fetch_instagram_memes_job(self):
        """Job to fetch Instagram memes - runs in separate thread to avoid blocking"""
        try:
            logger.info(f"[Instagram Scheduler] Starting Instagram meme fetch at {datetime.now()}")
            
            # Submit the fetch task to thread pool to avoid blocking the main thread
            future = fetch_executor.submit(self._fetch_instagram_memes_worker)
            
            # Add callback to log completion
            def log_completion(fut):
                try:
                    fut.result()  # This will raise any exception that occurred
                    logger.info(f"[Instagram Scheduler] Instagram meme fetch completed successfully at {datetime.now()}")
                except Exception as e:
                    logger.error(f"[Instagram Scheduler] Instagram meme fetch failed: {e}")
            
            future.add_done_callback(log_completion)
            
        except Exception as e:
            logger.error(f"[Instagram Scheduler] Critical error in Instagram fetch job: {e}")
    
    def _fetch_instagram_memes_worker(self):
        """Worker function that runs in separate thread to fetch Instagram memes"""
        try:
            # Use the existing Instagram batch function
            fetch_and_store_instagram_memes_batch()
            
            logger.info(f"[Instagram Scheduler] Instagram meme fetch worker completed at {datetime.now()}")
            
        except Exception as e:
            logger.error(f"[Instagram Scheduler] Critical error in Instagram fetch worker: {e}")
            raise
    
    def get_job_status(self):
        """Get the status of scheduled jobs"""
        if not self.is_running:
            return {"status": "stopped", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "jobs": jobs
        }
    
    def trigger_manual_fetch(self, source="reddit"):
        """Manually trigger a fetch job - runs in separate thread to avoid blocking"""
        try:
            if source.lower() == "reddit":
                logger.info("[Manual Trigger] Starting manual Reddit fetch")
                self.fetch_reddit_memes_job()
            elif source.lower() == "instagram":
                logger.info("[Manual Trigger] Starting manual Instagram fetch")
                self.fetch_instagram_memes_job()
            else:
                logger.error(f"[Manual Trigger] Unknown source: {source}")
                return False
            return True
        except Exception as e:
            logger.error(f"[Manual Trigger] Error in manual fetch: {e}")
            return False
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Meme scheduler stopped")
            
            # Shutdown the thread pool
            fetch_executor.shutdown(wait=True)
            logger.info("Thread pool shutdown completed")
        else:
            logger.info("Scheduler is not running")

# Global scheduler instance
meme_scheduler = MemeScheduler() 