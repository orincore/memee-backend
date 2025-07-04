from fastapi import APIRouter, Query, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
from app.models.meme import Meme
from app.services.supabase_service import (
    get_memes_by_category, like_meme, unlike_meme, get_meme_like_count, get_meme_by_id,
    save_meme, unsave_meme, get_saved_memes, get_saved_meme_ids, upload_meme, get_my_memes,
    edit_meme, delete_meme, get_meme_counts_batch, get_supabase
)
from app.routes.auth import get_current_user
import cloudinary.uploader

router = APIRouter(prefix="/memes", tags=["Memes"])

@router.get("/{category}", response_model=List[Meme])
def get_memes(
    category: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    after: str = Query(None, description="Fetch memes newer than this ISO timestamp"),
    random: bool = Query(False, description="Return memes in random order"),
    exclude_ids: str = Query("", description="Comma-separated meme IDs to exclude"),
    user=Depends(get_current_user)
):
    try:
        exclude_ids = exclude_ids or ""
        exclude_ids_list = [int(i) for i in exclude_ids.split(",") if i.strip()]
        memes = get_memes_by_category(category, page, page_size, after, random, exclude_ids_list)
        
        # Get all like counts in batch (much more efficient than individual queries)
        meme_ids = [meme.id for meme in memes if meme.id is not None]
        counts = get_meme_counts_batch(meme_ids)
        like_counts = counts["like_counts"]
        save_counts = counts["save_counts"]
        
        # Add like_count and save_count for each meme
        for meme in memes:
            meme_id = meme.id
            if meme_id is not None:
                meme.like_count = like_counts.get(meme_id, 0)
                meme.save_count = save_counts.get(meme_id, 0)
            else:
                meme.like_count = 0
                meme.save_count = 0
                
        return memes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{meme_id}/like")
def like_meme_endpoint(meme_id: int, user=Depends(get_current_user)):
    user_id = user['sub']
    return like_meme(user_id, meme_id)

@router.post("/{meme_id}/unlike")
def unlike_meme_endpoint(meme_id: int, user=Depends(get_current_user)):
    user_id = user['sub']
    return unlike_meme(user_id, meme_id)

@router.get("/{meme_id}/likes")
def meme_like_count(meme_id: int, user=Depends(get_current_user)):
    count = get_meme_like_count(meme_id)
    return {"meme_id": meme_id, "like_count": count}

@router.get("/id/{meme_id}")
def get_meme(meme_id: int, user=Depends(get_current_user)):
    meme = get_meme_by_id(meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    like_count = get_meme_like_count(meme_id)
    # Count saves
    save_count = len(get_supabase().table("meme_saves").select("id").eq("meme_id", meme_id).execute().data or [])
    meme["like_count"] = like_count
    meme["save_count"] = save_count
    return meme

@router.post("/{meme_id}/save")
def save_meme_endpoint(meme_id: int, user=Depends(get_current_user)):
    user_id = user['sub']
    return save_meme(user_id, meme_id)

@router.post("/{meme_id}/unsave")
def unsave_meme_endpoint(meme_id: int, user=Depends(get_current_user)):
    user_id = user['sub']
    return unsave_meme(user_id, meme_id)

@router.get("/saved")
def get_saved_memes_endpoint(user=Depends(get_current_user)):
    user_id = user['sub']
    return get_saved_memes(user_id)

@router.get("/saved/ids")
def get_saved_memes_full_endpoint(user=Depends(get_current_user)):
    user_id = user['sub']
    meme_ids = get_saved_meme_ids(user_id)
    if not meme_ids:
        return []
    memes = get_supabase().table("memes").select("*").in_("id", meme_ids).execute().data
    
    # Get all like counts in batch (much more efficient than individual queries)
    counts = get_meme_counts_batch(meme_ids)
    like_counts = counts["like_counts"]
    save_counts = counts["save_counts"]
    
    # Add like_count and save_count for each meme
    for meme in memes:
        meme_id = meme.get('id')
        if meme_id is not None:
            meme['like_count'] = like_counts.get(meme_id, 0)
            meme['save_count'] = save_counts.get(meme_id, 0)
        else:
            meme['like_count'] = 0
            meme['save_count'] = 0
    return memes

@router.post("/upload")
def upload_meme_endpoint(
    title: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    uploader_id = user['sub']
    uploader_username = user.get('username', None)
    # Upload file to Cloudinary
    upload_result = cloudinary.uploader.upload(file.file, resource_type="auto")
    file_url = upload_result["secure_url"]
    meme = upload_meme(title, category, file_url, uploader_id, uploader_username)
    return meme

@router.get("/my")
def get_my_memes_endpoint(user=Depends(get_current_user)):
    uploader_id = user['sub']
    print(f"[DEBUG] /memes/my called with uploader_id: '{uploader_id}'")
    
    memes = get_my_memes(uploader_id)
    print(f"[DEBUG] get_my_memes returned: {len(memes)} memes")
    
    if memes:
        print(f"[DEBUG] First meme: {memes[0]}")
    
    # Get all like counts in batch (much more efficient than individual queries)
    meme_ids = []
    for meme in memes:
        meme_id = meme.get('id')
        if meme_id is not None:
            meme_ids.append(int(meme_id))
    
    print(f"[DEBUG] meme_ids for batch query: {meme_ids}")
    
    counts = get_meme_counts_batch(meme_ids)
    like_counts = counts["like_counts"]
    save_counts = counts["save_counts"]
    
    # Add like_count and save_count for each meme
    for meme in memes:
        meme_id = meme.get('id')
        if meme_id is not None:
            meme['like_count'] = like_counts.get(meme_id, 0)
            meme['save_count'] = save_counts.get(meme_id, 0)
        else:
            meme['like_count'] = 0
            meme['save_count'] = 0
    
    print(f"[DEBUG] Final response: {len(memes)} memes")
    return memes

@router.put("/{meme_id}")
def edit_meme_endpoint(meme_id: int, title: str = Form(None), category: str = Form(None), user=Depends(get_current_user)):
    uploader_id = user['sub']
    return edit_meme(meme_id, uploader_id, title, category)

@router.delete("/{meme_id}")
def delete_meme_endpoint(meme_id: int, user=Depends(get_current_user)):
    uploader_id = user['sub']
    return delete_meme(meme_id, uploader_id)

@router.get("/my-uploads")
def get_my_uploads_endpoint(user=Depends(get_current_user)):
    """
    Get all memes uploaded by the currently logged-in user.
    Returns: List of memes with id, cloudinary_url, like_count, save_count
    """
    try:
        uploader_id = user['sub']
        print(f"[DEBUG] /memes/my-uploads called with uploader_id: '{uploader_id}'")
        
        # Get memes directly from database
        supabase = get_supabase()
        
        # First check if user has any memes
        check_query = supabase.table("memes").select("id").eq("uploader_id", uploader_id).limit(1).execute()
        print(f"[DEBUG] Check query found: {len(check_query.data)} memes")
        
        if not check_query.data:
            print(f"[DEBUG] No memes found for user {uploader_id}")
            return []
        
        # Get all memes for this user
        memes_query = supabase.table("memes").select("*").eq("uploader_id", uploader_id).order("timestamp", desc=True).execute()
        memes = memes_query.data or []
        
        print(f"[DEBUG] Found {len(memes)} memes for user {uploader_id}")
        
        if memes:
            print(f"[DEBUG] First meme: {memes[0]}")
        
        # Get meme IDs for batch counting
        meme_ids = [meme['id'] for meme in memes if meme.get('id')]
        print(f"[DEBUG] Meme IDs: {meme_ids}")
        
        # Get like and save counts in batch
        counts = get_meme_counts_batch(meme_ids)
        like_counts = counts["like_counts"]
        save_counts = counts["save_counts"]
        
        # Add counts to each meme
        for meme in memes:
            meme_id = meme.get('id')
            if meme_id:
                meme['like_count'] = like_counts.get(meme_id, 0)
                meme['save_count'] = save_counts.get(meme_id, 0)
            else:
                meme['like_count'] = 0
                meme['save_count'] = 0
        
        print(f"[DEBUG] Returning {len(memes)} memes with counts")
        return memes
        
    except Exception as e:
        print(f"[DEBUG] Error in get_my_uploads_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user's uploads: {str(e)}")

@router.get("/debug/user/{user_id}/memes")
def debug_user_memes(user_id: str):
    """
    Debug endpoint to test database query with any user ID
    """
    try:
        print(f"[DEBUG] Testing database query for user_id: {user_id}")
        
        supabase = get_supabase()
        
        # Direct database query
        memes_query = supabase.table("memes").select("*").eq("uploader_id", user_id).order("timestamp", desc=True).execute()
        memes = memes_query.data or []
        
        print(f"[DEBUG] Database query returned: {len(memes)} memes")
        
        if memes:
            print(f"[DEBUG] First meme: {memes[0]}")
        
        # Get counts
        meme_ids = [meme['id'] for meme in memes if meme.get('id')]
        counts = get_meme_counts_batch(meme_ids)
        like_counts = counts["like_counts"]
        save_counts = counts["save_counts"]
        
        # Add counts to memes
        for meme in memes:
            meme_id = meme.get('id')
            if meme_id:
                meme['like_count'] = like_counts.get(meme_id, 0)
                meme['save_count'] = save_counts.get(meme_id, 0)
            else:
                meme['like_count'] = 0
                meme['save_count'] = 0
        
        return {
            "user_id": user_id,
            "meme_count": len(memes),
            "memes": memes
        }
        
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}") 