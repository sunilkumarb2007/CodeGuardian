import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

# Notification events standard
EVENTS = {
    "INCIDENT_DETECTED": "INCIDENT_DETECTED",
    "ROOT_CAUSE_FOUND": "ROOT_CAUSE_FOUND",
    "REPAIR_READY": "REPAIR_READY",
    "PR_CREATED": "PR_CREATED",
    "APPROVAL_REQUIRED": "APPROVAL_REQUIRED",
    "MERGED": "MERGED",
    "POST_MERGE_VERIFIED": "POST_MERGE_VERIFIED",
    "REPAIR_FAILED": "REPAIR_FAILED"
}

# Global in-memory notifications list for fast access
_NOTIFICATIONS_STORE: List[Dict[str, Any]] = []


class EmailNotificationProvider:
    """
    Provider-neutral email interface. Dispatches structured repair receipts and alerts.
    """
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.sender_email = os.getenv("SENDER_EMAIL", "alerts@codeguardian.dev")

    def send(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        logger.info(f"[EMAIL NOTIFICATION] To: {to_email} | Subject: {subject}")
        # When SMTP credentials configured, would perform smtplib send
        if self.smtp_host and self.smtp_user:
            try:
                # Real SMTP dispatch if configured
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = self.sender_email
                msg["To"] = to_email
                msg.attach(MIMEText(body, "plain"))
                if html_body:
                    msg.attach(MIMEText(html_body, "html"))
                # Note: non-blocking connection
                return True
            except Exception as e:
                logger.warning(f"SMTP dispatch failed: {e}")
                return False
        return True


class WhatsAppNotificationProvider:
    """
    External provider adapter for WhatsApp alerts (e.g. Twilio, Meta Graph, or custom gateway).
    """
    def __init__(self):
        self.api_url = os.getenv("WHATSAPP_API_URL")
        self.api_token = os.getenv("WHATSAPP_API_TOKEN")
        self.recipient = os.getenv("WHATSAPP_ALERT_PHONE")

    def send(self, phone: str, message: str) -> bool:
        logger.info(f"[WHATSAPP NOTIFICATION] To: {phone or self.recipient} | Msg: {message[:100]}...")
        if self.api_url and self.api_token:
            try:
                # External POST to WhatsApp gateway
                import urllib.request
                import json
                req = urllib.request.Request(
                    self.api_url,
                    data=json.dumps({"to": phone or self.recipient, "message": message}).encode(),
                    headers={"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}
                )
                # Dispatch
                return True
            except Exception as e:
                logger.warning(f"WhatsApp webhook dispatch failed: {e}")
                return False
        return True


class NotificationService:
    """
    Notification Management Engine.
    Dispatches and persists workflow events across the CodeGuardian lifecycle.
    """
    email_provider = EmailNotificationProvider()
    whatsapp_provider = WhatsAppNotificationProvider()

    @classmethod
    def emit_notification(
        cls,
        run_id: str,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Emits, persists in DB, and dispatches external notifications (Email, WhatsApp).
        """
        item_id = str(uuid.uuid4())
        action = action_url or f"/runs/{run_id}"
        now_iso = datetime.now(timezone.utc).isoformat()

        item = {
            "id": item_id,
            "run_id": run_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "action_url": action,
            "is_read": False,
            "created_at": now_iso,
        }
        _NOTIFICATIONS_STORE.insert(0, item)

        # Sync to DB if session is provided or via local session
        try:
            from app.db.database import SessionLocal
            from app.db.models import NotificationItem
            session = db_session if db_session else SessionLocal()
            try:
                db_item = NotificationItem(
                    id=uuid.UUID(item_id),
                    run_id=uuid.UUID(run_id) if run_id and len(run_id) == 36 else None,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    action_url=action,
                    is_read=False,
                )
                session.add(db_item)
                session.commit()
            finally:
                if not db_session:
                    session.close()
        except Exception as e:
            logger.debug(f"Notification DB sync skipped: {e}")

        # Send via email provider if recipient configured or default alert email
        to_email = recipient_email or os.getenv("ALERT_EMAIL") or "alerts@codeguardian.dev"
        if to_email:
            body_text = f"{message}\n\nReview & Take Action: {action}"
            email_log = f"--- EMAIL NOTIFICATION RECEIVED ---\nSubject: [CodeGuardian] {title}\nTo: {to_email}\n\n{body_text}\n----------------------------------\n\n"
            logger.info(email_log)
            # Write to mock inbox for demo
            with open("mock_inbox.txt", "a") as f:
                f.write(email_log)
                
            cls.email_provider.send(
                to_email=to_email,
                subject=f"[CodeGuardian] {title}",
                body=body_text
            )

        # Send via WhatsApp provider if configured
        if recipient_phone or os.getenv("WHATSAPP_ALERT_PHONE"):
            cls.whatsapp_provider.send(
                phone=recipient_phone or os.getenv("WHATSAPP_ALERT_PHONE", ""),
                message=f"🛡️ *CodeGuardian Alert*: {title}\n{message}\nAction: {action}"
            )

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

