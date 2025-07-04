import os
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from app.services.reddit_service import fetch_and_store_memes
import random
from app.services.gemini_service import search_indian_memes_on_reddit
from app.services.supabase_service import insert_meme, get_supabase, get_meme_counts_batch
import cloudinary.uploader
from datetime import datetime
from app.meme_subreddits import MEME_SUBREDDITS
from app.routes.auth import get_current_user
from app.services.instagram_service import scrape_and_upload_instagram_memes, scrape_and_upload_instagram_memes_instagrapi
from pydantic import BaseModel
from typing import List
from app.models.meme import Meme

router = APIRouter(prefix="/fetch-memes", tags=["Fetch Memes"])

class InstagramScrapeRequest(BaseModel):
    instagram_page: str
    max_posts: int = 10

@router.post("/instagram")
def fetch_instagram_memes(
    req: InstagramScrapeRequest,
    user=Depends(get_current_user)
):
    session_file = "session-adarsh_7094_"
    try:
        results = scrape_and_upload_instagram_memes(
            instagram_username=req.instagram_page,
            session_file=session_file,
            max_posts=req.max_posts
        )
        return {"uploaded_memes": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/instagram/instagrapi")
def fetch_instagram_memes_instagrapi(
    req: InstagramScrapeRequest,
    user=Depends(get_current_user)
):
    try:
        results = scrape_and_upload_instagram_memes_instagrapi(
            instagram_username=req.instagram_page,
            max_posts=req.max_posts
        )
        
        # Save memes to database
        saved_count = 0
        for meme in results:
            try:
                # Check if meme already exists to avoid duplicates
                existing = get_supabase().table("memes").select("id").eq("reddit_post_url", meme["instagram_post_url"]).execute()
                if not existing.data:
                    get_supabase().table("memes").insert({
                        "title": meme["caption"] or "",
                        "cloudinary_url": meme["cloudinary_url"],
                        "reddit_post_url": meme["instagram_post_url"],
                        "category": "instagram",
                        "subreddit": "instagram",  # Required field
                        "timestamp": datetime.utcnow().isoformat(),
                        "uploader_id": user.get("id") if user else None,
                        "uploader_username": user.get("username") if user else None
                    }).execute()
                    saved_count += 1
            except Exception as insert_e:
                print(f"Error inserting meme: {insert_e} | Data: {meme}")
                continue
        
        return {
            "uploaded_memes": results,
            "saved_to_database": saved_count,
            "total_fetched": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{category}")
def fetch_memes(
    category: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    try:
        subreddit_name = random.choice(MEME_SUBREDDITS)
        background_tasks.add_task(fetch_and_store_memes, category, subreddit_name)
        return {"message": f"Fetching memes for category '{category}' from subreddit '{subreddit_name}' started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gemini")
def fetch_memes_gemini(user=Depends(get_current_user)):
    try:
        memes = search_indian_memes_on_reddit()
        inserted_count = 0
        for meme in memes:
            image_url = meme.get("image_url")
            title = meme.get("title")
            post_url = meme.get("post_url")
            subreddit = meme.get("subreddit")
            if not image_url or not title or not post_url or not subreddit:
                continue
            # Upload to Cloudinary
            try:
                upload_result = cloudinary.uploader.upload(image_url, resource_type="auto")
                cloudinary_url = upload_result["secure_url"]
            except Exception:
                continue
            # Store in Supabase
            meme_data = {
                "title": title,
                "cloudinary_url": cloudinary_url,
                "reddit_post_url": post_url,
                "subreddit": subreddit,
                "category": "gemini",
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                insert_meme(meme_data)
                inserted_count += 1
            except Exception:
                continue
        return {"message": f"Inserted {inserted_count} new memes from Gemini."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feed", response_model=List[Meme])
def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    exclude_ids: str = Query("", description="Comma-separated meme IDs to exclude"),
    user=Depends(get_current_user)
):
    try:
        exclude_ids_list = [int(i) for i in exclude_ids.split(",") if i.strip()]
        
        # Fetch all memes from Supabase
        memes_resp = get_supabase().table("memes").select("*").execute()
        memes = memes_resp.data or []
        
        # Exclude already seen memes
        if exclude_ids_list:
            memes = [m for m in memes if m.get("id") not in exclude_ids_list]
        
        # Get all like counts in batch (much more efficient than individual queries)
        meme_ids = [m["id"] for m in memes if m.get("id") is not None]
        counts = get_meme_counts_batch(meme_ids)
        like_counts = counts["like_counts"]
        save_counts = counts["save_counts"]
        
        # Calculate trending score: recency + like count
        import time, datetime
        for m in memes:
            meme_id = m.get("id")
            if meme_id is not None:
                m["like_count"] = like_counts.get(meme_id, 0)
                m["save_count"] = save_counts.get(meme_id, 0)
            else:
                m["like_count"] = 0
                m["save_count"] = 0
            
            ts = m.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    try:
                        dt = datetime.datetime.fromisoformat(ts)
                    except Exception:
                        dt = datetime.datetime.utcnow()
                else:
                    dt = ts
                m["trending_score"] = m["like_count"] * 10 + int(time.mktime(dt.timetuple()))
            else:
                m["trending_score"] = m["like_count"] * 10
        
        # Sort by trending score descending
        memes.sort(key=lambda m: m["trending_score"], reverse=True)
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        return memes[start:end]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 