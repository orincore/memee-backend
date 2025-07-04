import os
from supabase import create_client
from app.models.friend import FriendRequest, Friend
from app.models.user import UserOut
from typing import List
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials are not set in environment variables.")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_friend_request(from_user_id: int, to_user_id: int) -> FriendRequest:
    data = {
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        "status": "pending",
        "timestamp": datetime.utcnow().isoformat()
    }
    resp = supabase.table("friend_requests").insert(data).execute()
    return FriendRequest(**resp.data[0])

def respond_friend_request(request_id: int, accept: bool) -> FriendRequest:
    status = "accepted" if accept else "rejected"
    resp = supabase.table("friend_requests").update({"status": status}).eq("id", request_id).execute()
    fr = FriendRequest(**resp.data[0])
    if accept:
        # Add to friends table (bidirectional)
        supabase.table("friends").insert({"user_id": fr.from_user_id, "friend_id": fr.to_user_id, "since": datetime.utcnow().isoformat()}).execute()
        supabase.table("friends").insert({"user_id": fr.to_user_id, "friend_id": fr.from_user_id, "since": datetime.utcnow().isoformat()}).execute()
    return fr

def list_friends(user_id: int) -> List[UserOut]:
    resp = supabase.table("friends").select("friend_id").eq("user_id", user_id).execute()
    friend_ids = [f["friend_id"] for f in resp.data]
    if not friend_ids:
        return []
    users = supabase.table("users").select("*").in_("id", friend_ids).execute()
    return [UserOut(**u) for u in users.data]

def search_users(query: str) -> List[UserOut]:
    resp = supabase.table("users").select("*").ilike("username", f"%{query}%").execute()
    return [UserOut(**u) for u in resp.data] 