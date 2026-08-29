from fastapi import APIRouter
from typing import Optional
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("")
def list_notifications(unread_only: bool = False):
    """
    Returns list of active notifications and unread counter.
    """
    items = NotificationService.get_notifications(unread_only=unread_only)
    unread_count = NotificationService.get_unread_count()
    return {
        "notifications": items,
        "unread_count": unread_count
    }

@router.post("/{notification_id}/read")
def mark_read(notification_id: str):
    """
    Marks a notification as read (or 'all').
    """
    success = NotificationService.mark_as_read(notification_id)
    return {
        "success": success,
        "unread_count": NotificationService.get_unread_count()
    }
