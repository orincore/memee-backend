import os
import instaloader
import cloudinary
import cloudinary.uploader
from typing import List, Dict
from instagrapi import Client
from pathlib import Path
from instagrapi.exceptions import ClientError, ClientLoginRequired
import random
from app.services.supabase_service import get_supabase
import time
from datetime import datetime
import logging

# Reduce verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("cloudinary").setLevel(logging.WARNING)
logging.getLogger("instagrapi").setLevel(logging.WARNING)
logging.getLogger("instaloader").setLevel(logging.WARNING)

# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def scrape_and_upload_instagram_memes(
    instagram_username: str,
    session_file: str,
    max_posts: int = 10
) -> List[Dict]:
    """
    Scrape latest posts from an Instagram page and upload to Cloudinary.
    Returns a list of dicts: { 'cloudinary_url', 'caption', 'instagram_post_url' }
    """
    L = instaloader.Instaloader()
    # Load session from custom file in project root
    L.load_session_from_file(instagram_username, filename=session_file)
    profile = instaloader.Profile.from_username(L.context, instagram_username)
    results = []
    count = 0
    for post in profile.get_posts():
        if count >= max_posts:
            break
        # Download to temp file
        L.download_post(post, target="_tmp")
        # Find the downloaded file
        local_file = None
        for ext in (".jpg", ".mp4"):
            candidate = f"_tmp/{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S_UTC')}{ext}"
            if os.path.exists(candidate):
                local_file = candidate
                break
        if not local_file:
            continue
        # Upload to Cloudinary
        resource_type = "video" if local_file.endswith(".mp4") else "image"
        upload_result = cloudinary.uploader.upload(local_file, resource_type=resource_type)
        # Clean up local file
        os.remove(local_file)
        # Add to results
        results.append({
            "cloudinary_url": upload_result["secure_url"],
            "caption": post.caption,
            "instagram_post_url": f"https://instagram.com/p/{post.shortcode}/"
        })
        count += 1
    # Optionally, clean up the _tmp directory
    try:
        os.rmdir("_tmp")
    except Exception:
        pass
    return results

# New instagrapi-based function
def scrape_and_upload_instagram_memes_instagrapi(
    instagram_username: str,
    max_posts: int = 10
) -> List[Dict]:
    """
    Scrape latest posts from an Instagram page using instagrapi and upload to Cloudinary.
    Returns a list of dicts: { 'cloudinary_url', 'caption', 'instagram_post_url' }
    """
    ig_user = os.getenv('INSTA_USERNAME')
    ig_pass = os.getenv('INSTA_PASSWORD')
    cl = Client()
    cl.request_timeout = 20  # Increase timeout to 20 seconds for downloads
    settings_path = Path('instagrapi_settings.json')
    if settings_path.exists():
        cl.load_settings(settings_path)
    cl.login(ig_user, ig_pass)
    cl.dump_settings(settings_path)
    try:
        user_id = cl.user_id_from_username(instagram_username)
        try:
            medias = cl.user_medias(user_id, max_posts)
        except KeyError as e:
            print(f"KeyError in user_medias: {e}, trying user_medias_v1 fallback")
            medias = cl.user_medias_v1(user_id, max_posts)
    except Exception as e:
        print(f"Error fetching medias: {e}")
        raise RuntimeError(f"Failed to fetch posts for {instagram_username}: {e}")
    if not medias:
        raise RuntimeError(f"No posts found for user {instagram_username} or the account is private/restricted.")
    results = []
    for media in medias:
        url = None
        if media.media_type == 1:
            url = str(media.thumbnail_url) if media.thumbnail_url else None
        else:
            url = str(media.video_url) if media.video_url else None
        if not url:
            continue
        local_filename = url.split("?")[0].split("/")[-1]
        if media.media_type == 1:
            downloaded_path = cl.photo_download_by_url(url, filename=local_filename)
        else:
            downloaded_path = cl.video_download_by_url(url, filename=local_filename)
        resource_type = "video" if media.media_type != 1 else "image"
        upload_result = cloudinary.uploader.upload(downloaded_path, resource_type=resource_type)
        os.remove(downloaded_path)
        results.append({
            "cloudinary_url": upload_result["secure_url"],
            "caption": media.caption_text,
            "instagram_post_url": f"https://instagram.com/p/{media.code}/"
        })
    return results

INSTAGRAM_ACCOUNTS = [
    "theanimeboiis",
    "weebily",
    "idleglance",
    "isekaij",
    "spiffydripmemes",
    "good.life.good.thoughts",
    "meme_in_my_way",
    "memes_with_aaruhi",
    "societyofmature",
    "alwayschillin"
    # Add more accounts as needed
]

def fetch_and_store_instagram_memes_batch():
    """
    Fetch posts from a random Instagram account and save to Supabase, skipping already-saved posts.
    Optimized for non-blocking operation with reduced limits.
    """
    try:
        accounts = INSTAGRAM_ACCOUNTS[:]
        random.shuffle(accounts)
        
        for account in accounts:
            try:
                # Reduced max_posts for faster processing
                memes = scrape_and_upload_instagram_memes_instagrapi(account, max_posts=10)
                new_count = 0
                
                for meme in memes:
                    # Check by Instagram post URL to avoid duplicates
                    existing = get_supabase().table("memes").select("id").eq("reddit_post_url", meme["instagram_post_url"]).execute()
                    if not existing.data:
                        try:
                            get_supabase().table("memes").insert({
                                "title": meme["caption"] or "",
                                "cloudinary_url": meme["cloudinary_url"],
                                "reddit_post_url": meme["instagram_post_url"],
                                "category": "instagram",
                                "subreddit": "instagram",  # Ensure required field
                                "timestamp": datetime.utcnow().isoformat(),
                                "uploader_id": None,
                                "uploader_username": None
                            }).execute()
                            new_count += 1
                            
                            # Limit total memes per batch for faster processing
                            if new_count >= 10:
                                break
                                
                        except Exception as insert_e:
                            print(f"[Instagram Batch] Insert error: {insert_e} | Data: {meme}")
                            
                print(f"[Instagram Batch] Account: {account}, New memes saved: {new_count}")
                break  # Only fetch from one account per run
                
            except Exception as e:
                print(f"[Instagram Batch] Error with account {account}: {e}")
                continue
                
        print(f"[Instagram Batch] Batch run complete at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"[Instagram Batch] Critical error: {e}")
        raise 