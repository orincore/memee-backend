import os
import praw
import cloudinary.uploader
from app.services.supabase_service import insert_meme
from datetime import datetime
import prawcore
import random
from app.meme_subreddits import MEME_SUBREDDITS
import logging

# Reduce verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("cloudinary").setLevel(logging.WARNING)
logging.getLogger("praw").setLevel(logging.WARNING)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".mp4"}

# Map categories to subreddits (updated with user-specified subreddits)
CATEGORY_SUBREDDITS = {
    "dark": [
        "DarkMemes_",
        "DarkMemesPh",
        "darkmemers",
        "darkmemes",  # keep existing for completeness
        "dankmemes"   # keep existing for completeness
    ],
    "comedy": [
        "memes",
        "funny"
    ],
    "wholesome": [
        "wholesomememes"
    ],
    "general": [
        "memes"
    ]
}

def fetch_and_store_memes(category: str, subreddit_name: str = None):
    """Fetch and store memes from Reddit - optimized for non-blocking operation"""
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        
        # Use MEME_SUBREDDITS for subreddit list if not provided
        if subreddit_name:
            subreddits = [subreddit_name]
        else:
            subreddits = MEME_SUBREDDITS
            print(f"[fetch_and_store_memes] Using MEME_SUBREDDITS: {subreddits}")
        
        if not subreddits:
            return
        
        inserted_count = 0
        banned_subreddits = set()
        max_retries = 20  # Reduced retry limit for faster operation
        retries = 0
        
        while inserted_count < 30 and retries < max_retries:  # Reduced limit for faster operation
            # Shuffle and make a copy to avoid retrying the same subreddit in the same loop
            subreddits_to_try = subreddits[:]
            random.shuffle(subreddits_to_try)
            
            for subreddit_name in subreddits_to_try:
                if subreddit_name in banned_subreddits:
                    continue
                    
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    new_memes_this_sub = 0
                    
                    # Reduced limit for faster processing
                    for submission in subreddit.hot(limit=25):
                        url = submission.url
                        if not any(url.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                            continue
                            
                        # Check for duplicate in DB before uploading to Cloudinary
                        from app.services.supabase_service import supabase
                        reddit_post_url = f"https://reddit.com{submission.permalink}"
                        existing = supabase.table("memes").select("id").eq("reddit_post_url", reddit_post_url).execute()
                        if existing.data and len(existing.data) > 0:
                            continue
                            
                        # Upload to Cloudinary with timeout
                        try:
                            upload_result = cloudinary.uploader.upload(url, resource_type="auto", timeout=10)
                            cloudinary_url = upload_result["secure_url"]
                        except Exception as e:
                            print(f"[fetch_and_store_memes] Cloudinary upload failed for {url}: {e}")
                            continue
                            
                        # Store in Supabase
                        meme_data = {
                            "title": submission.title,
                            "cloudinary_url": cloudinary_url,
                            "reddit_post_url": reddit_post_url,
                            "subreddit": subreddit_name,
                            "category": category,
                            "timestamp": datetime.utcfromtimestamp(submission.created_utc).isoformat()
                        }
                        
                        try:
                            from app.services.supabase_service import insert_meme
                            insert_meme(meme_data)
                            inserted_count += 1
                            new_memes_this_sub += 1
                            
                            if inserted_count >= 30:  # Reduced limit
                                print(f"[fetch_and_store_memes] Inserted {inserted_count} new memes. Stopping fetch.")
                                return
                                
                        except Exception as e:
                            print(f"[fetch_and_store_memes] Insert failed: {e}")
                            continue
                            
                    if new_memes_this_sub == 0:
                        print(f"[fetch_and_store_memes] No new memes found in subreddit '{subreddit_name}'. Moving to next subreddit.")
                        continue
                    else:
                        print(f"[fetch_and_store_memes] Inserted {new_memes_this_sub} new memes from subreddit '{subreddit_name}'. Total so far: {inserted_count}")
                        
                except prawcore.exceptions.Redirect:
                    print(f"[fetch_and_store_memes] Subreddit '{subreddit_name}' caused a redirect (does not exist or is banned). Skipping permanently.")
                    banned_subreddits.add(subreddit_name)
                    continue
                except Exception as e:
                    if '404' in str(e):
                        print(f"[fetch_and_store_memes] Subreddit '{subreddit_name}' returned 404. Skipping permanently.")
                        banned_subreddits.add(subreddit_name)
                    else:
                        print(f"[fetch_and_store_memes] Error processing subreddit '{subreddit_name}': {e}")
                    continue
                    
            retries += 1
            
        print(f"[fetch_and_store_memes] Finished fetching. Total unique memes inserted: {inserted_count}")
        
    except Exception as e:
        print(f"[fetch_and_store_memes] Critical error: {e}")
        raise 