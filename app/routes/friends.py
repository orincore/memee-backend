from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.friend_service import send_friend_request, respond_friend_request, list_friends, search_users
from typing import List
from app.routes.auth import get_current_user

router = APIRouter(prefix="/friends", tags=["Friends"])

@router.post("/request")
def send_request(to_user_id: int, user=Depends(get_current_user)):
    user_id = user['sub']
    if to_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a friend.")
    return send_friend_request(user_id, to_user_id)

@router.post("/respond")
def respond(request_id: int, accept: bool, user=Depends(get_current_user)):
    user_id = user['sub']
    return respond_friend_request(request_id, accept)

@router.get("/list", response_model=List[dict])
def friends(user=Depends(get_current_user)):
    user_id = user['sub']
    return [f.dict() for f in list_friends(user_id)]

@router.get("/search", response_model=List[dict])
def search(q: str = Query(..., min_length=1), user=Depends(get_current_user)):
    return [u.dict() for u in search_users(q)] 