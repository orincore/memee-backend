from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import UserSignup, UserOut
from app.services.user_service import create_user, authenticate_user, get_user_by_email
from typing import Optional
from datetime import datetime
from app.services.email_service import send_otp_email, send_welcome_email
import logging
from app.services.jwt_service import create_access_token, verify_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return payload

@router.post("/signup", response_model=UserOut)
def signup(
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    date_of_birth: str = Form(...),
    gender: Optional[str] = Form(None),
    meme_choices: str = Form(...),  # comma-separated
    profile_pic: Optional[UploadFile] = File(None)
):
    user = UserSignup(
        name=name,
        username=username,
        email=email,
        phone=phone,
        password=password,
        date_of_birth=datetime.strptime(date_of_birth, "%Y-%m-%d").date(),
        gender=gender,
        meme_choices=[c.strip() for c in meme_choices.split(",")],
        profile_pic=None
    )
    user_out = create_user(user, profile_pic.file if profile_pic else None)
    # Send OTP email
    db_user = get_user_by_email(email)
    if db_user and db_user.otp:
        send_otp_email(email, db_user.otp)
    # Optionally, return JWT token (uncomment if you want auto-login after signup)
    # access_token = create_access_token({"sub": user_out.id, "email": user_out.email})
    # return {"access_token": access_token, "token_type": "bearer", "user": user_out}
    return user_out

@router.post("/login")
def login(
    login_id: str = Form(...),  # email or username
    password: str = Form(...)
):
    # Try email first
    user = get_user_by_email(login_id)
    if not user:
        # Try username
        from app.services.user_service import get_user_by_username
        user = get_user_by_username(login_id)
    if not user or not authenticate_user(user.email, password):
        raise HTTPException(status_code=401, detail="Invalid credentials or email not verified.")
    # Create JWT token
    access_token = create_access_token({"sub": user.id, "email": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/verify-otp")
def verify_otp(email: str = Form(...), otp: str = Form(...)):
    import logging
    logging.info("TEST: Entered verify_otp endpoint")
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")
    # Mark as verified
    from app.services.user_service import supabase
    supabase.table("users").update({"is_verified": True, "otp": None}).eq("email", email).execute()
    # Send welcome email with logging
    logging.info(f"Attempting to send welcome email to {email} ({user.username})")
    try:
        send_welcome_email(email, user.username)
        logging.info(f"Welcome email sent to {email}")
    except Exception as e:
        logging.error(f"Failed to send welcome email to {email}: {e}")
    return {"message": "Email verified successfully."}

@router.post("/resend-otp")
def resend_otp(email: str = Form(...)):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    from app.services.user_service import generate_otp, supabase
    otp = generate_otp()
    supabase.table("users").update({"otp": otp}).eq("email", email).execute()
    send_otp_email(email, otp)
    return {"message": "OTP resent successfully."} 