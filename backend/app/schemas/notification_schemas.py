from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class NotificationOut(BaseModel):
    id: int
    patient_id: int
    title: str
    message: str
    type: str
    priority: str
    is_read: bool
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class NotificationCreate(BaseModel):
    patient_id: int
    title: str
    message: str
    type: Optional[str] = "info"
    priority: Optional[str] = "normal"
    send_email: Optional[bool] = False
