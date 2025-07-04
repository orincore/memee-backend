from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FriendRequest(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    status: str  # pending, accepted, rejected
    timestamp: datetime

class Friend(BaseModel):
    id: int
    user_id: int
    friend_id: int
    since: datetime 