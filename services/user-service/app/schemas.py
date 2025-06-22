from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    role: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    role: str

    class Config:
        orm_mode = True

class UserProfileBase(BaseModel):
    full_name: str
    bio: Optional[str] = None
    skills: Optional[str] = None
    portfolio_url: Optional[str] = None
    is_freelancer: bool = False
    is_client: bool = False

class UserProfileCreate(UserProfileBase):
    user_id: int

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True 