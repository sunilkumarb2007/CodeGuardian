import hmac
import hashlib
import logging
from typing import Optional
from fastapi import APIRouter, Request, Header, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

def verify_signature(payload_body: bytes, signature_header: Optional[str]) -> bool:
    """Verify GitHub webhook HMAC SHA256 signature."""
    secret = settings.github_webhook_secret
    if not secret:
        # If no secret is configured, allow in development but warn
        logger.warning("GITHUB_WEBHOOK_SECRET not configured. Skipping HMAC validation.")
        return True

    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header on GitHub webhook.")
        return False

    parts = signature_header.split("sha256=")
    if len(parts) != 2:
        return False

    expected_signature = parts[1]
    computed_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_signature, expected_signature)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
):
    """
    Production GitHub Webhook receiver.
    Accepts repository events (push, pull_request, workflow_run, installation, ping).
    """
    body = await request.body()

    # Validate HMAC signature
    if not verify_signature(body, x_hub_signature_256):
        logger.warning(f"GitHub webhook rejected: invalid signature for delivery {x_github_delivery}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid HMAC signature",
        )

    event_name = x_github_event or "unknown"
    logger.info(f"GitHub webhook received: event={event_name}, delivery={x_github_delivery}")

    try:
        payload = await request.json() if body else {}
    except Exception:
        payload = {}

    # Handle ping event
    if event_name == "ping":
        return {
            "status": "accepted",
            "message": "Pong! Webhook successfully configured.",
            "zen": payload.get("zen"),
            "hook_id": payload.get("hook_id"),
        }

    # Handle installation event
    if event_name == "installation":
        action = payload.get("action")
        inst_id = payload.get("installation", {}).get("id")
        logger.info(f"GitHub App installation event: action={action}, installation_id={inst_id}")
        return {
            "status": "accepted",
            "event": "installation",
            "action": action,
            "installation_id": inst_id,
        }

    # Handle push or pull_request
    repo_info = payload.get("repository", {})
    repo_name = repo_info.get("full_name")
    
    return {
        "status": "accepted",
        "event": event_name,
        "repository": repo_name,
        "delivery_id": x_github_delivery,
    }
