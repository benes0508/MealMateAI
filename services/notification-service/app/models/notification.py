from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    MEAL_REMINDER = "meal_reminder"
    GROCERY_LIST = "grocery_list"
    SYSTEM = "system"
    CUSTOM = "custom"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class NotificationBase(BaseModel):
    user_id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    related_entity_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    
class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: str
    created_at: datetime
    read: bool = False
    read_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class NotificationUpdate(BaseModel):
    read: Optional[bool] = None
