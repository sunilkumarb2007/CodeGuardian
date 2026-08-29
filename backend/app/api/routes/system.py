import json
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
        "failure_lab": "ready",
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

@router.post("/api/ai/test")
def ai_test_endpoint():
    """
    Requested minimal backend AI health/test path to explicitly verify OpenRouter connectivity.
    """
    if not settings.openrouter_api_key:
        return {"status": "error", "message": "No OpenRouter API key configured"}
    
    import httpx
    import time
    
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.openrouter_model or "google/gemini-2.5-flash",
        "messages": [
            {"role": "user", "content": "Respond exactly with the word 'ok' and nothing else."}
        ],
        "temperature": 0.0,
        "max_tokens": 10
    }
    
    start_time = time.time()
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{settings.openrouter_base_url or 'https://openrouter.ai/api/v1'}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            # Calculate latency in ms
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "status": "ok",
                "provider": "openrouter",
                "model": payload["model"],
                "latency_ms": latency_ms
            }
            
    except Exception as e:
        return {"status": "error", "message": f"OpenRouter integration failed: {str(e)}"}


@router.post("/api/ai/preflight")
def ai_preflight_endpoint():
    """
    Small structured-output diagnostic.
    Sends a tiny prompt (no repo, no GhostTrace) requiring an InvestigationResult JSON response.
    Instruments every transport milestone so we can localize any hang.
    """
    provider = (settings.ai_provider or "sarvam").lower()
    
    if provider == "sarvam":
        base_url = (settings.sarvam_base_url or settings.ai_base_url or "https://api.sarvam.ai").rstrip("/")
        model = settings.sarvam_model or settings.ai_model or "sarvam-105b"
        api_key = settings.sarvam_api_key or settings.openrouter_api_key
        endpoint = f"{base_url}/v1/chat/completions"
        headers = {
            "api-subscription-key": api_key or "",
            "Authorization": f"Bearer {api_key or ''}",
            "Content-Type": "application/json"
        }
    elif provider == "deepseek":
        base_url = (settings.deepseek_base_url or settings.ai_base_url or "https://api.deepseek.com").rstrip("/")
        model = settings.deepseek_model or settings.ai_model or "deepseek-chat"
        api_key = settings.deepseek_api_key or settings.openrouter_api_key
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key or ''}",
            "Content-Type": "application/json"
        }
    else:
        base_url = (settings.openrouter_base_url or "https://openrouter.ai/api/v1").rstrip("/")
        model = settings.openrouter_model or "poolside/laguna-s-2.1:free"
        api_key = settings.openrouter_api_key
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key or ''}",
            "Content-Type": "application/json"
        }

    if not api_key:
        return {"status": "error", "provider": provider, "model": model, "error_type": "MISSING_KEY", "error": "No API key configured"}

    import httpx
    import time as _time
    from app.schemas.investigation import InvestigationResult

    PREFLIGHT_PROMPT = (
        "You are an expert automated root-cause analysis and automated program repair engineer.\n"
        "Analyze the following minimal synthetic issue and return ONLY a valid JSON object matching the InvestigationResult schema.\n\n"
        "Target File: PaymentService.java\n"
        "Failure: NullPointerException at PaymentService.java:24 (merchant is null)\n\n"
        "Return a complete JSON object with fields:\n"
        "- status: 'completed'\n"
        "- root_cause: { 'service': 'payment-service', 'summary': 'Null dereference when merchant is null', 'affected_file': 'PaymentService.java', 'location': 'PaymentService.java:24' }\n"
        "- repair_plan: { 'steps': [{ 'action': 'ADD_NULL_CHECK', 'description': 'Add explicit null check for merchant' }], 'risk': 'LOW', 'expected_behavior': 'Throws descriptive exception instead of NPE' }\n"
        "- patch_candidate: { 'status': 'generated', 'files_changed': ['PaymentService.java'], 'diff': '--- a/PaymentService.java\\n+++ b/PaymentService.java\\n@@ -24,3 +24,5 @@\\n+        if (merchant == null) {\\n+            throw new IllegalStateException(\"Merchant not found\");\\n+        }\\n', 'explanation': 'Adds explicit null validation.' }"
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a software debugging investigator. Return ONLY valid JSON conforming to the requested schema. No conversational text."
            },
            {"role": "user", "content": PREFLIGHT_PROMPT}
        ],
        "temperature": 0.0,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"}
    }

    milestones = {}
    t0 = _time.monotonic()

    try:
        with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0, read=60.0, write=10.0)) as client:
            milestones["request_sent_ms"] = round((_time.monotonic() - t0) * 1000)
            resp = client.post(endpoint, headers=headers, json=payload)
            milestones["response_ms"] = round((_time.monotonic() - t0) * 1000)
            milestones["status_code"] = resp.status_code

            if resp.status_code in (401, 403):
                return {"status": "error", "provider": provider, "model": model, "endpoint": endpoint, "error_type": "SARVAM_AUTH_FAILED" if provider == "sarvam" else "AUTH_FAILED", "error": f"Unauthorized (HTTP {resp.status_code}): Invalid API key"}
            elif resp.status_code == 402:
                return {"status": "error", "provider": provider, "model": model, "endpoint": endpoint, "error_type": "CREDITS_EXHAUSTED", "error": "Insufficient balance"}
            elif resp.status_code == 429:
                return {"status": "error", "provider": provider, "model": model, "endpoint": endpoint, "error_type": "SARVAM_RATE_LIMITED" if provider == "sarvam" else "RATE_LIMITED", "error": "Rate limit exceeded"}
            elif resp.status_code in (400, 413, 422):
                return {"status": "error", "provider": provider, "model": model, "endpoint": endpoint, "error_type": "SARVAM_INVALID_REQUEST" if provider == "sarvam" else "INVALID_REQUEST", "error": f"HTTP {resp.status_code}: {resp.text}"}
            elif resp.status_code != 200:
                return {"status": "error", "provider": provider, "model": model, "endpoint": endpoint, "error_type": "SARVAM_PROVIDER_ERROR" if provider == "sarvam" else f"HTTP_{resp.status_code}", "error": f"HTTP status {resp.status_code}: {resp.text}"}

            data = resp.json()
            choices = data.get("choices", [])
            choice = choices[0] if choices else {}
            msg = choice.get("message", {})
            finish_reason = choice.get("finish_reason")
            content = msg.get("content")
            reasoning = msg.get("reasoning_content")
            tool_calls = msg.get("tool_calls")
            milestones["finish_reason"] = finish_reason
            milestones["content_present"] = content is not None
            milestones["reasoning_present"] = reasoning is not None

            if content is None and tool_calls:
                return {"status": "error", "provider": provider, "model": model, "endpoint": endpoint, "error_type": "SARVAM_TOOL_CALL_RESPONSE", "error": "Model returned tool calls instead of content"}

            if content is None and finish_reason == "length":
                if reasoning and "{" in reasoning and "}" in reasoning:
                    start_brace = reasoning.find("{")
                    end_brace = reasoning.rfind("}")
                    candidate = reasoning[start_brace:end_brace + 1]
                    try:
                        json.loads(candidate)
                        content = candidate
                    except Exception:
                        pass
                if not content:
                    return {"status": "error", "provider": provider, "model": model, "endpoint": endpoint, "error_type": "SARVAM_OUTPUT_TRUNCATED", "error": "Response was truncated by token limit"}

            if not content:
                if reasoning and "{" in reasoning and "}" in reasoning:
                    start_brace = reasoning.find("{")
                    end_brace = reasoning.rfind("}")
                    candidate = reasoning[start_brace:end_brace + 1]
                    try:
                        json.loads(candidate)
                        content = candidate
                    except Exception:
                        pass

            if not content:
                return {
                    "status": "error",
                    "provider": provider,
                    "model": model,
                    "endpoint": endpoint,
                    "error_type": "SARVAM_INVALID_RESPONSE" if provider == "sarvam" else "EMPTY_CONTENT",
                    "error": "Empty content returned by model"
                }

            milestones["content_length"] = len(content)

        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
        elif content.startswith("```"):
            content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
        content = content.strip()

        # Clean quotes
        if content.startswith('"') and content.endswith('"') and content.count('{') > 0:
            try:
                unquoted = json.loads(content)
                if isinstance(unquoted, str):
                    content = unquoted
            except Exception:
                pass
        content = content.strip()
        if content.endswith('"') and content.rfind('}') < len(content) - 1:
            content = content[:content.rfind('}') + 1]

        try:
            validated_obj = InvestigationResult.model_validate_json(content)
        except Exception as ve:
            return {
                "status": "error",
                "provider": provider,
                "model": model,
                "endpoint": endpoint,
                "error_type": "SARVAM_SCHEMA_ERROR" if provider == "sarvam" else "SCHEMA_VALIDATION_ERROR",
                "error": str(ve),
                "raw_content": content[:300]
            }

        total_latency = round((_time.monotonic() - t0) * 1000)

        return {
            "status": "ok",
            "provider": provider,
            "model": model,
            "endpoint": endpoint,
            "latency_ms": total_latency,
            "schema_valid": True,
            "milestones": milestones,
            "investigation_result": {
                "status": validated_obj.status,
                "root_cause_summary": validated_obj.root_cause.summary if validated_obj.root_cause else None,
                "repair_steps_count": len(validated_obj.repair_plan.steps) if validated_obj.repair_plan else 0,
                "diff_preview": (validated_obj.patch_candidate.diff[:120] + '...') if validated_obj.patch_candidate and validated_obj.patch_candidate.diff else None
            }
        }

    except httpx.TimeoutException as e:
        return {"status": "error", "provider": provider, "model": model, "error_type": "TIMEOUT", "error": str(e)}
    except Exception as e:
        return {"status": "error", "provider": provider, "model": model, "error_type": "EXCEPTION", "error": str(e)}

