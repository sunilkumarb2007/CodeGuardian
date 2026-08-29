import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Global in-memory notifications list for fast access + DB sync
_NOTIFICATIONS_STORE: List[Dict[str, Any]] = []

class NotificationService:
    """
    Notification Management Engine.
    Dispatches and persists workflow events across the CodeGuardian lifecycle.
    """

    @classmethod
    def emit_notification(
        cls,
        run_id: str,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Emits and stores a notification event.
        """
        item = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "action_url": action_url or f"/runs/{run_id}",
            "is_read": False,
            "created_at": datetime.utcnow().isoformat()
        }
        _NOTIFICATIONS_STORE.insert(0, item)
        logger.info(f"Notification emitted: [{notification_type}] {title} (Run: {run_id})")
        return item

    @classmethod
    def get_notifications(cls, unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieves notifications list.
        """
        if unread_only:
            return [n for n in _NOTIFICATIONS_STORE if not n.get("is_read")]
        return _NOTIFICATIONS_STORE[:50]

    @classmethod
    def mark_as_read(cls, notification_id: str) -> bool:
        """
        Marks a single notification or all notifications as read.
        """
        if notification_id == "all":
            for n in _NOTIFICATIONS_STORE:
                n["is_read"] = True
            return True

        for n in _NOTIFICATIONS_STORE:
            if n["id"] == notification_id:
                n["is_read"] = True
                return True
        return False

    @classmethod
    def get_unread_count(cls) -> int:
        return sum(1 for n in _NOTIFICATIONS_STORE if not n.get("is_read"))
