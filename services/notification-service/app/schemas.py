from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class NotificationBase(BaseModel):
    recipient_id: int
    type: str
    message: str

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        orm_mode = True

class NotificationPreferenceBase(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True

class NotificationPreferenceCreate(NotificationPreferenceBase):
    user_id: int

class NotificationPreference(NotificationPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None 