import os
from app.models.user import UserSignup, UserOut, UserInDB
from supabase import create_client
from passlib.context import CryptContext
import cloudinary.uploader
import random, string
from typing import Optional
from datetime import date, datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials are not set in environment variables.")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def create_user(user: UserSignup, profile_pic_file=None) -> UserOut:
    # Upload profile pic if provided
    profile_pic_url = None
    if profile_pic_file:
        upload_result = cloudinary.uploader.upload(profile_pic_file, folder="profile_pics")
        profile_pic_url = upload_result["secure_url"]
    # Supabase Auth signup
    auth_resp = supabase.auth.sign_up({
        "email": user.email,
        "password": user.password,
        "options": {
            "data": {
                "name": user.name,
                "username": user.username,
                "phone": user.phone,
                "profile_pic": profile_pic_url or user.profile_pic,
                "date_of_birth": user.date_of_birth.isoformat() if isinstance(user.date_of_birth, (date, datetime)) else user.date_of_birth,
                "gender": user.gender,
                "meme_choices": user.meme_choices,
            }
        }
    })
    if not auth_resp.user:
        raise Exception(f"Supabase Auth signup failed: {auth_resp}")
    user_id = auth_resp.user.id
    # Generate OTP
    otp = generate_otp()
    # Insert into users table
    profile_data = {
        "id": user_id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "hashed_password": hash_password(user.password),
        "profile_pic": profile_pic_url or user.profile_pic,
        "date_of_birth": user.date_of_birth.isoformat() if isinstance(user.date_of_birth, (date, datetime)) else user.date_of_birth,
        "gender": user.gender,
        "meme_choices": user.meme_choices,
        "otp": otp,
        "is_verified": False
    }
    resp = supabase.table("users").insert(profile_data).execute()
    return UserOut(id=user_id, **{k: profile_data[k] for k in UserOut.__fields__ if k != "id"})

def get_user_by_email(email: str) -> Optional[UserInDB]:
    resp = supabase.table("users").select("*").eq("email", email).single().execute()
    if not resp.data:
        return None
    return UserInDB(**resp.data)

def get_user_by_username(username: str) -> Optional[UserInDB]:
    resp = supabase.table("users").select("*").eq("username", username).single().execute()
    if not resp.data:
        return None
    return UserInDB(**resp.data)

def authenticate_user(email: str, password: str) -> Optional[UserOut]:
    user = get_user_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_verified:
        return None
    return UserOut(**user.dict()) 