import os
from typing import List

# Scheduler Configuration
SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"

# Night fetching schedule (3 AM for 30 minutes)
NIGHT_FETCH_START_HOUR = int(os.getenv("NIGHT_FETCH_START_HOUR", "3"))  # 3 AM
NIGHT_FETCH_DURATION_MINUTES = int(os.getenv("NIGHT_FETCH_DURATION_MINUTES", "30"))  # 30 minutes
NIGHT_FETCH_INTERVAL_MINUTES = int(os.getenv("NIGHT_FETCH_INTERVAL_MINUTES", "5"))  # Fetch every 5 minutes during night window

# Legacy interval settings (kept for backward compatibility but not used)
REDDIT_FETCH_INTERVAL_MINUTES = int(os.getenv("REDDIT_FETCH_INTERVAL_MINUTES", "15"))
INSTAGRAM_FETCH_INTERVAL_MINUTES = int(os.getenv("INSTAGRAM_FETCH_INTERVAL_MINUTES", "15"))

# Reddit fetch configuration
REDDIT_CATEGORIES = [
    "funny", "memes", "dank", "wholesome", "gaming", "anime", 
    "programming", "science", "history", "politics", "sports"
]

# Number of categories to fetch per cycle (randomly selected)
REDDIT_CATEGORIES_PER_CYCLE = int(os.getenv("REDDIT_CATEGORIES_PER_CYCLE", "3"))

# Delay between category fetches (to avoid rate limiting)
REDDIT_FETCH_DELAY_SECONDS = int(os.getenv("REDDIT_FETCH_DELAY_SECONDS", "2"))

# Instagram fetch configuration
INSTAGRAM_ACCOUNTS_PER_CYCLE = int(os.getenv("INSTAGRAM_ACCOUNTS_PER_CYCLE", "1"))
INSTAGRAM_POSTS_PER_ACCOUNT = int(os.getenv("INSTAGRAM_POSTS_PER_ACCOUNT", "20"))

# Logging configuration
SCHEDULER_LOG_LEVEL = os.getenv("SCHEDULER_LOG_LEVEL", "INFO")

# Error handling
MAX_RETRIES_PER_CATEGORY = int(os.getenv("MAX_RETRIES_PER_CATEGORY", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "30")) 