from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class Meme(BaseModel):
    id: Optional[int]
    title: str
    cloudinary_url: HttpUrl
    reddit_post_url: Optional[HttpUrl] = None
    category: str
    subreddit: Optional[str] = None
    timestamp: datetime
    like_count: Optional[int] = 0
    save_count: Optional[int] = 0
    uploader_username: Optional[str] = None
    uploader_id: Optional[str] = None 