import os
from typing import List, Optional, Dict
from app.models.meme import Meme
from supabase import create_client, Client
from datetime import datetime
import random as pyrandom
import logging

# Reduce verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)

def get_supabase():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials are not set in environment variables.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_memes_by_category(category: str, page: int, page_size: int, after: Optional[str] = None, random: bool = False, exclude_ids: Optional[list] = None) -> List[Meme]:
    try:
        if exclude_ids is None:
            exclude_ids = []
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = get_supabase().table("memes").select("*").eq("category", category)
        if after:
            query = query.gt("timestamp", after)
        # Always order by id descending (latest first)
        query = query.order("id", desc=True)
        # Fetch a larger pool if exclude_ids is provided
        fetch_size = (end - start + 1) * 3 if exclude_ids else (end - start + 1)
        response = query.range(0, fetch_size - 1).execute()
        memes = [Meme(**item) for item in response.data]
        if exclude_ids:
            memes = [m for m in memes if m.id not in exclude_ids]
        if random:
            pyrandom.shuffle(memes)
        # Return the requested page
        return memes[start:end+1]
    except Exception as e:
        raise RuntimeError(f"Failed to fetch memes: {e}")

def insert_meme(meme_data: dict):
    try:
        # Check for duplicate by reddit_post_url only if it's not None
        if meme_data.get("reddit_post_url"):
            existing = get_supabase().table("memes").select("id").eq("reddit_post_url", meme_data["reddit_post_url"]).execute()
            if existing.data and len(existing.data) > 0:
                # Duplicate found, skip insert
                print(f"[insert_meme] Duplicate meme found for URL: {meme_data['reddit_post_url']}. Skipping insert.")
                return
        get_supabase().table("memes").insert(meme_data).execute()
    except Exception as e:
        raise RuntimeError(f"Failed to insert meme: {e}")

def like_meme(user_id: str, meme_id: int):
    try:
        # Insert like if not exists
        get_supabase().table("meme_likes").insert({"user_id": user_id, "meme_id": meme_id}).execute()
        return {"message": "Meme liked."}
    except Exception as e:
        # If unique constraint fails, user already liked
        if "duplicate key value violates unique constraint" in str(e):
            return {"message": "Already liked."}
        raise RuntimeError(f"Failed to like meme: {e}")

def unlike_meme(user_id: str, meme_id: int):
    try:
        get_supabase().table("meme_likes").delete().eq("user_id", user_id).eq("meme_id", meme_id).execute()
        return {"message": "Meme unliked."}
    except Exception as e:
        raise RuntimeError(f"Failed to unlike meme: {e}")

def get_meme_like_count(meme_id: int) -> int:
    try:
        resp = get_supabase().table("meme_likes").select("id").eq("meme_id", meme_id).execute()
        return len(resp.data) if resp.data else 0
    except Exception as e:
        raise RuntimeError(f"Failed to get like count: {e}")

def get_meme_by_id(meme_id: int):
    try:
        resp = get_supabase().table("memes").select("*").eq("id", meme_id).single().execute()
        if not resp.data:
            return None
        return resp.data
    except Exception as e:
        raise RuntimeError(f"Failed to get meme: {e}")

def save_meme(user_id: str, meme_id: int):
    try:
        get_supabase().table("meme_saves").insert({"user_id": user_id, "meme_id": meme_id}).execute()
        return {"message": "Meme saved."}
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            return {"message": "Already saved."}
        raise RuntimeError(f"Failed to save meme: {e}")

def unsave_meme(user_id: str, meme_id: int):
    try:
        get_supabase().table("meme_saves").delete().eq("user_id", user_id).eq("meme_id", meme_id).execute()
        return {"message": "Meme unsaved."}
    except Exception as e:
        raise RuntimeError(f"Failed to unsave meme: {e}")

def get_saved_memes(user_id: str):
    try:
        resp = get_supabase().table("meme_saves").select("meme_id").eq("user_id", user_id).execute()
        meme_ids = [int(row["meme_id"]) for row in resp.data if row.get("meme_id") is not None]
        print("DEBUG: meme_ids for user", user_id, meme_ids)
        if not meme_ids:
            return []
        memes_resp = get_supabase().table("memes").select("*").in_("id", meme_ids).execute()
        print("DEBUG: memes found", memes_resp.data)
        return memes_resp.data
    except Exception as e:
        raise RuntimeError(f"Failed to get saved memes: {e}")

def get_saved_meme_ids(user_id: str):
    try:
        resp = get_supabase().table("meme_saves").select("meme_id").eq("user_id", user_id).execute()
        meme_ids = [row["meme_id"] for row in resp.data]
        return meme_ids
    except Exception as e:
        raise RuntimeError(f"Failed to get saved meme ids: {e}")

def upload_meme(title: str, category: str, file_url: str, uploader_id: str, uploader_username: str):
    try:
        supabase = get_supabase()
        meme_data = {
            "title": title,
            "category": category,
            "cloudinary_url": file_url,
            "reddit_post_url": None,
            "subreddit": None,  # Add subreddit field for user uploads
            "timestamp": datetime.utcnow().isoformat(),
            "uploader_id": uploader_id,
            "uploader_username": uploader_username
        }
        resp = supabase.table("memes").insert(meme_data).execute()
        return resp.data[0] if resp.data else meme_data
    except Exception as e:
        raise RuntimeError(f"Failed to upload meme: {e}")

def get_my_memes(uploader_id: str):
    try:
        print(f"[DEBUG] get_my_memes called with uploader_id: '{uploader_id}'")
        supabase = get_supabase()
        
        # First, let's check what memes exist in the database
        all_memes = supabase.table("memes").select("id, title, uploader_id").execute()
        print(f"[DEBUG] Total memes in database: {len(all_memes.data)}")
        
        memes_with_uploader = [m for m in all_memes.data if m.get('uploader_id')]
        print(f"[DEBUG] Memes with uploader_id: {len(memes_with_uploader)}")
        
        if memes_with_uploader:
            print(f"[DEBUG] Sample memes with uploader_id: {memes_with_uploader[:3]}")
        
        # Now query for the specific user's memes
        resp = supabase.table("memes").select("*").eq("uploader_id", uploader_id).order("timestamp", desc=True).execute()
        print(f"[DEBUG] Query result: {len(resp.data)} memes found for uploader_id '{uploader_id}'")
        
        if resp.data:
            print(f"[DEBUG] First meme found: {resp.data[0]}")
        else:
            print(f"[DEBUG] No memes found for uploader_id '{uploader_id}'")
            
        return resp.data
    except Exception as e:
        print(f"[DEBUG] Error in get_my_memes: {e}")
        raise RuntimeError(f"Failed to get user's memes: {e}")

def edit_meme(meme_id: int, uploader_id: str, title: Optional[str] = None, category: Optional[str] = None):
    try:
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if category is not None:
            update_data["category"] = category
        if not update_data:
            return {"message": "Nothing to update."}
        resp = get_supabase().table("memes").update(update_data).eq("id", meme_id).eq("uploader_id", uploader_id).execute()
        return resp.data[0] if resp.data else {"message": "No meme updated."}
    except Exception as e:
        raise RuntimeError(f"Failed to edit meme: {e}")

def delete_meme(meme_id: int, uploader_id: str):
    try:
        resp = get_supabase().table("memes").delete().eq("id", meme_id).eq("uploader_id", uploader_id).execute()
        return {"message": "Meme deleted."}
    except Exception as e:
        raise RuntimeError(f"Failed to delete meme: {e}")

def get_meme_counts_batch(meme_ids: List[int]) -> Dict[str, Dict[int, int]]:
    """
    Get like and save counts for multiple memes in batch.
    Returns: {"like_counts": {meme_id: count}, "save_counts": {meme_id: count}}
    """
    like_counts = {}
    save_counts = {}
    
    if not meme_ids:
        return {"like_counts": like_counts, "save_counts": save_counts}
    
    try:
        # Get all likes in one query
        likes_resp = get_supabase().table("meme_likes").select("meme_id").in_("meme_id", meme_ids).execute()
        likes_data = likes_resp.data or []
        
        # Count likes per meme
        for like in likes_data:
            meme_id = like["meme_id"]
            like_counts[meme_id] = like_counts.get(meme_id, 0) + 1
        
        # Get all saves in one query
        saves_resp = get_supabase().table("meme_saves").select("meme_id").in_("meme_id", meme_ids).execute()
        saves_data = saves_resp.data or []
        
        # Count saves per meme
        for save in saves_data:
            meme_id = save["meme_id"]
            save_counts[meme_id] = save_counts.get(meme_id, 0) + 1
            
    except Exception as e:
        print(f"Error getting batch counts: {e}")
    
    return {"like_counts": like_counts, "save_counts": save_counts}