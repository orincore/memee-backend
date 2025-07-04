from fastapi import APIRouter, HTTPException, Depends
from app.routes.auth import get_current_user
from app.services.async_scheduler_service import async_meme_scheduler
import logging

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])

@router.get("/status")
def get_scheduler_status(user=Depends(get_current_user)):
    """Get the current status of the meme scheduler"""
    try:
        status = async_meme_scheduler.get_job_status()
        return {
            "scheduler_status": status["status"],
            "jobs": status["jobs"],
            "message": "Scheduler status retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@router.post("/start")
def start_scheduler(user=Depends(get_current_user)):
    """Start the meme scheduler"""
    try:
        async_meme_scheduler.start()
        return {
            "message": "Meme scheduler started successfully",
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/stop")
def stop_scheduler(user=Depends(get_current_user)):
    """Stop the meme scheduler"""
    try:
        async_meme_scheduler.stop()
        return {
            "message": "Meme scheduler stopped successfully",
            "status": "stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.post("/trigger/reddit")
def trigger_reddit_fetch(user=Depends(get_current_user)):
    """Manually trigger a Reddit meme fetch"""
    try:
        success = async_meme_scheduler.trigger_manual_fetch("reddit")
        if success:
            return {
                "message": "Reddit meme fetch triggered successfully",
                "status": "triggered"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to trigger Reddit fetch")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger Reddit fetch: {str(e)}")

@router.post("/trigger/instagram")
def trigger_instagram_fetch(user=Depends(get_current_user)):
    """Manually trigger an Instagram meme fetch"""
    try:
        success = async_meme_scheduler.trigger_manual_fetch("instagram")
        if success:
            return {
                "message": "Instagram meme fetch triggered successfully",
                "status": "triggered"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to trigger Instagram fetch")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger Instagram fetch: {str(e)}")

@router.post("/trigger/all")
def trigger_all_fetches(user=Depends(get_current_user)):
    """Manually trigger both Reddit and Instagram meme fetches"""
    try:
        reddit_success = async_meme_scheduler.trigger_manual_fetch("reddit")
        instagram_success = async_meme_scheduler.trigger_manual_fetch("instagram")
        
        results = {
            "reddit": "success" if reddit_success else "failed",
            "instagram": "success" if instagram_success else "failed",
            "message": "Manual fetch triggered for all sources"
        }
        
        if not reddit_success or not instagram_success:
            raise HTTPException(status_code=500, detail=f"Some fetches failed: {results}")
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger fetches: {str(e)}")

@router.post("/trigger/night-session")
def trigger_night_session(user=Depends(get_current_user)):
    """Manually trigger the night fetch session (30 minutes of continuous fetching)"""
    try:
        success = async_meme_scheduler.trigger_manual_fetch("night_session")
        if success:
            return {
                "message": "Night fetch session triggered successfully",
                "status": "triggered",
                "duration": "30 minutes",
                "note": "Session will run for 30 minutes with 5-minute intervals"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to trigger night session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger night session: {str(e)}") 