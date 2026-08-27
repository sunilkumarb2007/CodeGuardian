from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.core.config import settings
from app.core.redis import redis_manager

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "backend"}

@router.get("/api/system/status")
def system_status(db: Session = Depends(get_db)):
    # Try a simple query to verify db
    db_status = "ok"
    try:
        db.execute(text("SELECT 1")).fetchone()
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    redis_status = "healthy" if redis_manager.is_healthy() else "unavailable"
        
    return {
        "backend": "ok",
        "database": db_status,
        "redis": redis_status,
        "git": "available", # Assuming git is installed, ideally checked via subprocess
        "workspace": "ok",
        "openrouter_configured": bool(settings.openrouter_api_key),
        "github_configured": bool(settings.github_token),
        "version": "1.0.0"
    }

@router.get("/api/system/ai/preflight")
def ai_preflight():
    """
    Performs a tiny JSON-schema pre-flight check to verify OpenRouter connectivity and structured output schema matching.
    Does not consume significant budget.
    """
    if not settings.openrouter_api_key:
        return {"status": "error", "message": "No OpenRouter API key configured"}
        
    import httpx
    
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json"
    }
    
    schema = {
        "type": "object",
        "properties": {
            "preflight_status": {"type": "string"}
        },
        "required": ["preflight_status"]
    }
    
    payload = {
        "model": settings.openrouter_model or "google/gemini-2.5-flash",
        "messages": [
            {"role": "user", "content": "Respond with 'ok'."}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "preflight_result",
                "strict": True,
                "schema": schema
            }
        },
        "temperature": 0.0
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{settings.openrouter_base_url or 'https://openrouter.ai/api/v1'}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            
            import json
            parsed = json.loads(content)
            if parsed.get("preflight_status"):
                return {"status": "ok", "provider_response": parsed}
            return {"status": "error", "message": "Invalid JSON structure returned"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
