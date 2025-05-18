from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from typing import List, Optional
from pydantic import EmailStr

from app.models.notification import (
    NotificationCreate, 
    Notification, 
    NotificationUpdate,
    NotificationResponse
)
from app.services.notification_service import NotificationService

router = APIRouter()
notification_service = NotificationService()

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    background_tasks: BackgroundTasks,
    notification: NotificationCreate = Body(...)
):
    """
    Create a new notification and schedule it to be sent
    """
    return await notification_service.create_notification(background_tasks, notification)


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all notifications, with optional filtering by user_id
    """
    return await notification_service.get_notifications(user_id, skip, limit)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int):
    """
    Get a specific notification by ID
    """
    notification = await notification_service.get_notification_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(notification_id: int, notification_update: NotificationUpdate):
    """
    Update an existing notification
    """
    notification = await notification_service.update_notification(notification_id, notification_update)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.delete("/{notification_id}")
async def delete_notification(notification_id: int):
    """
    Delete a notification
    """
    success = await notification_service.delete_notification(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted successfully"}


@router.post("/send_email")
async def send_email(
    background_tasks: BackgroundTasks,
    email: EmailStr = Body(...),
    subject: str = Body(...),
    content: str = Body(...)
):
    """
    Send an email directly
    """
    await notification_service.send_email(background_tasks, email, subject, content)
    return {"message": "Email scheduled for delivery"}