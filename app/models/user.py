from pydantic import BaseModel, EmailStr, HttpUrl, validator
from typing import Optional, List
from datetime import date

class UserSignup(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone: str
    password: str
    profile_pic: Optional[HttpUrl]
    date_of_birth: date
    gender: Optional[str]
    meme_choices: List[str]

    @validator('date_of_birth')
    def check_age(cls, v):
        from datetime import date
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 16:
            raise ValueError('You must be at least 16 years old to sign up.')
        return v 

class UserOut(BaseModel):
    id: str
    name: str
    username: str
    email: EmailStr
    phone: str
    profile_pic: Optional[HttpUrl]
    date_of_birth: date
    gender: Optional[str]
    meme_choices: List[str]

class UserInDB(BaseModel):
    id: str
    name: str
    username: str
    email: EmailStr
    phone: str
    hashed_password: str
    profile_pic: Optional[HttpUrl]
    date_of_birth: date
    gender: Optional[str]
    meme_choices: List[str]
    otp: Optional[str]
    is_verified: bool = False 