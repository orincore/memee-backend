import os
import time
import random
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.services.reddit_service import fetch_and_store_memes
from app.services.instagram_service import fetch_and_store_instagram_memes_batch
from app.meme_subreddits import MEME_SUBREDDITS
from app.config.scheduler_config import (
    SCHEDULER_ENABLED, NIGHT_FETCH_START_HOUR, NIGHT_FETCH_DURATION_MINUTES, 
    NIGHT_FETCH_INTERVAL_MINUTES, REDDIT_CATEGORIES, REDDIT_CATEGORIES_PER_CYCLE, 
    REDDIT_FETCH_DELAY_SECONDS, SCHEDULER_LOG_LEVEL
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
fetch_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="meme_fetch")

class AsyncMemeScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.loop = None
        
    def start(self):
        """Start the scheduler"""
        if not self.is_running and SCHEDULER_ENABLED:
            try:
                # Get or create event loop
                try:
                    self.loop = asyncio.get_event_loop()
                except RuntimeError:
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
                
                # Schedule Reddit meme fetching at 3 AM daily
                self.scheduler.add_job(
                    func=self.start_night_fetch_session,
                    trigger=CronTrigger(hour=NIGHT_FETCH_START_HOUR, minute=0),
                    id='night_fetch_session',
                    name='Night Fetch Session (3 AM)',
                    replace_existing=True
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info(f"Async meme scheduler started successfully - Night fetch at {NIGHT_FETCH_START_HOUR}:00 AM for {NIGHT_FETCH_DURATION_MINUTES} minutes")
                
                # No initial fetch - only fetch at night
                logger.info("Scheduler configured for night-only fetching. No initial fetch.")
                
            except Exception as e:
                logger.error(f"Failed to start async scheduler: {e}")
                raise
        elif not SCHEDULER_ENABLED:
            logger.info("Scheduler is disabled in configuration")
        else:
            logger.info("Scheduler is already running")
    
    async def start_night_fetch_session(self):
        """Start the night fetch session at 3 AM - runs for 30 minutes"""
        try:
            logger.info(f"[Night Session] Starting night fetch session at {datetime.now()}")
            
            # Calculate end time for the session
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=NIGHT_FETCH_DURATION_MINUTES)
            
            logger.info(f"[Night Session] Session will run until {end_time.strftime('%H:%M:%S')}")
            
            # Start the night fetch loop
            await self._run_night_fetch_loop(start_time, end_time)
            
            logger.info(f"[Night Session] Night fetch session completed at {datetime.now()}")
            
        except Exception as e:
            logger.error(f"[Night Session] Critical error in night fetch session: {e}")
    
    async def _run_night_fetch_loop(self, start_time, end_time):
        """Run the night fetch loop for the specified duration"""
        while datetime.now() < end_time:
            try:
                # Fetch Reddit memes
                logger.info(f"[Night Session] Fetching Reddit memes...")
                await self.fetch_reddit_memes_job()
                
                # Wait a bit before Instagram fetch
                await asyncio.sleep(2)
                
                # Fetch Instagram memes
                logger.info(f"[Night Session] Fetching Instagram memes...")
                await self.fetch_instagram_memes_job()
                
                # Wait for next cycle (every 5 minutes during night session)
                logger.info(f"[Night Session] Waiting {NIGHT_FETCH_INTERVAL_MINUTES} minutes until next fetch...")
                await asyncio.sleep(NIGHT_FETCH_INTERVAL_MINUTES * 60)
                
            except Exception as e:
                logger.error(f"[Night Session] Error in fetch loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def fetch_reddit_memes_job(self):
        """Async job to fetch Reddit memes - runs in separate thread to avoid blocking"""
        try:
            logger.info(f"[Reddit Scheduler] Starting Reddit meme fetch at {datetime.now()}")
            
            # Run the fetch operation in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(fetch_executor, self._fetch_reddit_memes_worker)
            
            logger.info(f"[Reddit Scheduler] Reddit meme fetch completed successfully at {datetime.now()}")
            
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
    
    async def fetch_instagram_memes_job(self):
        """Async job to fetch Instagram memes - runs in separate thread to avoid blocking"""
        try:
            logger.info(f"[Instagram Scheduler] Starting Instagram meme fetch at {datetime.now()}")
            
            # Run the fetch operation in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(fetch_executor, self._fetch_instagram_memes_worker)
            
            logger.info(f"[Instagram Scheduler] Instagram meme fetch completed successfully at {datetime.now()}")
            
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
    
    async def trigger_manual_fetch_async(self, source="reddit"):
        """Manually trigger a fetch job - runs in separate thread to avoid blocking"""
        try:
            if source.lower() == "reddit":
                logger.info("[Manual Trigger] Starting manual Reddit fetch")
                await self.fetch_reddit_memes_job()
            elif source.lower() == "instagram":
                logger.info("[Manual Trigger] Starting manual Instagram fetch")
                await self.fetch_instagram_memes_job()
            elif source.lower() == "night_session":
                logger.info("[Manual Trigger] Starting manual night fetch session")
                await self.start_night_fetch_session()
            else:
                logger.error(f"[Manual Trigger] Unknown source: {source}")
                return False
            return True
        except Exception as e:
            logger.error(f"[Manual Trigger] Error in manual fetch: {e}")
            return False
    
    def trigger_manual_fetch(self, source="reddit"):
        """Synchronous wrapper for manual fetch trigger"""
        try:
            if self.loop and self.loop.is_running():
                # If we're in an async context, create a task
                asyncio.create_task(self.trigger_manual_fetch_async(source))
            else:
                # If we're not in an async context, run in executor
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.trigger_manual_fetch_async(source))
                finally:
                    loop.close()
            return True
        except Exception as e:
            logger.error(f"[Manual Trigger] Error in manual fetch: {e}")
            return False
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Async meme scheduler stopped")
            
            # Shutdown the thread pool
            fetch_executor.shutdown(wait=True)
            logger.info("Thread pool shutdown completed")
        else:
            logger.info("Scheduler is not running")

# Global scheduler instance
async_meme_scheduler = AsyncMemeScheduler() 