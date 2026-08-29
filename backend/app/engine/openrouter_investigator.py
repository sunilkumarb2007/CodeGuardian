import logging
import json
import time
import httpx
from typing import Optional

from app.core.config import settings
from app.schemas.investigation import InvestigationResult
from app.engine.investigator_provider import InvestigatorProvider

logger = logging.getLogger(__name__)

# Minimum time we will ever give a single AI attempt, even if the shared
# deadline has nearly expired.  Prevents httpx.Timeout(0) which disables
# the read timeout entirely.
_MIN_ATTEMPT_TIMEOUT = 30.0   # seconds
_CONNECT_TIMEOUT = 10.0       # seconds – connection must succeed quickly


class OpenRouterInvestigator(InvestigatorProvider):
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url
        self.site_url = settings.openrouter_site_url or "https://codeguardian.local"
        self.site_name = settings.openrouter_site_name or "CodeGuardian"

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def investigate(self, prompt: str, deadline: Optional[float] = None, on_milestone = None) -> Optional[InvestigationResult]:
        if not self.api_key:
            logger.warning("Cannot investigate: missing OpenRouter API key")
            raise RuntimeError("INVESTIGATOR_NOT_CONFIGURED")

        logger.info(f"Invoking OpenRouter model: {self.model}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
            "Content-Type": "application/json"
        }

        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "root_cause": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string"},
                        "summary": {"type": "string"},
                        "affected_file": {"type": "string"},
                        "location": {"type": "string"},
                        "confidence": {"type": "number"},
                        "failure_mechanism": {"type": "string"}
                    },
                    "required": ["service", "summary"]
                },
                "historical_reference": {
                    "type": "object",
                    "properties": {
                        "found": {"type": "boolean"},
                        "memory_status": {"type": "string"},
                        "applicability": {"type": "string"}
                    },
                    "required": ["found"]
                },
                "repair_plan": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string"},
                                    "description": {"type": "string"}
                                },
                                "required": ["action", "description"]
                            }
                        },
                        "risk": {"type": "string"},
                        "expected_behavior": {"type": "string"}
                    },
                    "required": ["steps", "risk", "expected_behavior"]
                },
                "patch_candidate": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "files_changed": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "diff": {"type": "string"},
                        "explanation": {"type": "string"}
                    },
                    "required": ["files_changed", "diff", "explanation"]
                },
                "verification_requirements": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "evidence_used": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["status", "root_cause", "repair_plan", "patch_candidate"]
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        # Some providers/models (e.g. poolside/laguna-s-2.1:free) do not support response_format json_schema
        if not ("laguna" in self.model.lower() or "free" in self.model.lower()):
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "investigation_result",
                    "strict": True,
                    "schema": schema
                }
            }

        payload_bytes = len(json.dumps(payload).encode('utf-8'))
        prompt_chars = len(prompt)
        logger.info(f"CODEGUARDIAN_REQUEST_SIZE: {payload_bytes} bytes (prompt length: {prompt_chars} chars)")

        logger.info("OPENROUTER_REQUEST_STARTED")
        logger.info(f"timestamp: {time.time()}")
        max_retries = 3

        # Use caller-supplied deadline or create a fresh one (fallback only)
        from app.core.execution_policy import ExecutionPolicy
        if deadline is None:
            deadline = time.monotonic() + ExecutionPolicy.AI_TOTAL_DEADLINE
            logger.warning("investigate() called without a shared deadline — using fresh budget")

        for attempt in range(max_retries):
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                logger.error('OPENROUTER_REQUEST_TIMEOUT: deadline already expired before attempt')
                raise RuntimeError('INVESTIGATION_TIMEOUT')

            # CRITICAL: clamp to _MIN_ATTEMPT_TIMEOUT floor so we never create
            # httpx.Timeout(negative) or httpx.Timeout(0) — both disable read timeout.
            capped = min(remaining_time, ExecutionPolicy.AI_REQUEST_TIMEOUT)
            attempt_timeout = max(capped, _MIN_ATTEMPT_TIMEOUT)
            if attempt_timeout > remaining_time:
                logger.warning(
                    f"OPENROUTER_TIMEOUT_FLOOR: remaining={remaining_time:.1f}s below "
                    f"minimum {_MIN_ATTEMPT_TIMEOUT}s — using floor"
                )

            timeout = httpx.Timeout(
                attempt_timeout,
                connect=_CONNECT_TIMEOUT,
                read=attempt_timeout,
                write=10.0
            )
            logger.info(
                f"OPENROUTER_ATTEMPT {attempt + 1}/{max_retries}: "
                f"timeout={attempt_timeout:.1f}s remaining={remaining_time:.1f}s"
            )

            with httpx.Client(timeout=timeout) as client:
                req_start = time.monotonic()
                content = None
                try:
                    logger.info("OPENROUTER_CONNECTING: opening stream to openrouter.ai")
                    if on_milestone:
                        on_milestone("system", "Connecting to OpenRouter", f"Connecting to {self.base_url} ({self.model})...")

                    with client.stream("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                        connect_ms = (time.monotonic() - req_start) * 1000
                        logger.info(
                            f"OPENROUTER_CONNECTED: headers received in {connect_ms:.0f}ms "
                            f"status={response.status_code}"
                        )
                        if on_milestone:
                            on_milestone("system", "OpenRouter connected", f"HTTP {response.status_code} received in {connect_ms/1000:.1f}s. Waiting for model response...")

                        if response.status_code == 429:
                            logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: RATE_LIMITED")
                            raise RuntimeError("RATE_LIMITED")
                        elif response.status_code == 401:
                            logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: OPENROUTER_AUTH_FAILED")
                            raise RuntimeError("OPENROUTER_AUTH_FAILED")
                        elif response.status_code == 402:
                            logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: OPENROUTER_CREDITS_EXHAUSTED")
                            raise RuntimeError("OPENROUTER_CREDITS_EXHAUSTED")
                        elif response.status_code == 403:
                            logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: OPENROUTER_AUTH_FAILED")
                            raise RuntimeError("OPENROUTER_AUTH_FAILED")
                        elif response.status_code == 408:
                            logger.error(f"OPENROUTER_REQUEST_TIMEOUT\nduration_ms: {connect_ms:.2f}")
                            raise RuntimeError("OPENROUTER_TIMEOUT")
                        elif response.status_code >= 500:
                            logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: OPENROUTER_PROVIDER_ERROR")
                            raise RuntimeError("OPENROUTER_PROVIDER_ERROR")

                        response.raise_for_status()

                        # Read body in chunks; check wall-clock deadline on every chunk
                        logger.info("OPENROUTER_READING_BODY: starting chunked read")
                        content_bytes = bytearray()
                        first_chunk = True
                        for chunk in response.iter_bytes(chunk_size=8192):
                            if first_chunk:
                                first_byte_ms = (time.monotonic() - req_start) * 1000
                                logger.info(f"OPENROUTER_FIRST_BYTE: {first_byte_ms:.0f}ms")
                                if on_milestone:
                                    on_milestone("analysis", "First token received", f"Model started generating output ({first_byte_ms/1000:.1f}s TTFT). Streaming response...")
                                first_chunk = False
                            if time.monotonic() > deadline:
                                logger.error(
                                    "OPENROUTER_REQUEST_TIMEOUT: wall-clock deadline exceeded during stream read"
                                )
                                raise RuntimeError('OPENROUTER_TIMEOUT')
                            content_bytes.extend(chunk)

                        body_ms = (time.monotonic() - req_start) * 1000
                        logger.info(
                            f"OPENROUTER_BODY_COMPLETE: {body_ms:.0f}ms "
                            f"body_size={len(content_bytes)}B"
                        )
                        if on_milestone:
                            on_milestone("output", "Model response complete", f"Stream complete ({len(content_bytes)/1024:.1f} KB in {body_ms/1000:.1f}s). Validating structured JSON...")

                        data = json.loads(content_bytes.decode('utf-8'))
                        content = data.get("choices", [{}])[0].get("message", {}).get("content")

                    if not content:
                        logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: Empty content")
                        raise RuntimeError("OPENROUTER_EMPTY_RESPONSE")

                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                        if content.endswith("```"):
                            content = content[:-3]
                    content = content.strip()

                    # Handle cases where model wraps or appends a trailing quote
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

                    logger.info("OPENROUTER_PARSE_STARTED")
                    parse_start = time.time()
                    result = InvestigationResult.model_validate_json(content)
                    parse_duration = (time.time() - parse_start) * 1000
                    logger.info(f"OPENROUTER_PARSE_COMPLETED\nduration_ms: {parse_duration:.2f}")

                    return result

                except httpx.HTTPStatusError as e:
                    # In a streaming request, e.response hasn't been read if we didn't call read()
                    err_msg = ""
                    try:
                        err_msg = e.response.read().decode('utf-8')
                    except Exception:
                        pass
                        
                    logger.error(
                        f"OPENROUTER_REQUEST_FAILED\nerror_type: HTTPStatusError {e.response.status_code}"
                    )
                    with open("debug_or.txt", "a") as f:
                        f.write(f"HTTP Error: {e.response.status_code} - {err_msg}\n")
                        
                    if e.response.status_code == 402:
                        raise RuntimeError("OPENROUTER_CREDITS_EXHAUSTED")
                    elif e.response.status_code == 429:
                        raise RuntimeError("RATE_LIMITED")
                    elif e.response.status_code in (401, 403):
                        raise RuntimeError("OPENROUTER_AUTH_FAILED")
                    elif e.response.status_code >= 500:
                        raise RuntimeError("OPENROUTER_PROVIDER_ERROR")
                        
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("OPENROUTER_PROVIDER_ERROR")

                except httpx.TimeoutException as e:
                    elapsed_ms = (time.monotonic() - req_start) * 1000
                    logger.error(
                        f"OPENROUTER_REQUEST_TIMEOUT: httpx timeout after {elapsed_ms:.0f}ms "
                        f"(attempt_timeout={attempt_timeout:.1f}s)"
                    )
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("INVESTIGATION_TIMEOUT")

                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    logger.error(f"INVESTIGATION_SCHEMA_ERROR: Failed to parse OpenRouter response: {e}")
                    if attempt < max_retries - 1:
                        logger.info("Attempting structured-output repair...")
                        payload["messages"].append({"role": "assistant", "content": content or ""})
                        payload["messages"].append({
                            "role": "user",
                            "content": (
                                f"Your previous response did not satisfy the required schema. "
                                f"Return only a JSON object conforming to the supplied JSON Schema. "
                                f"The validation failure was: {str(e)}"
                            )
                        })
                        continue
                    raise RuntimeError("INVESTIGATION_SCHEMA_ERROR") from e

                except RuntimeError:
                    raise

                except Exception as e:
                    logger.error(f"Error during OpenRouter investigation: {e}")
                    with open("debug_or.txt", "a") as f:
                        f.write(f"Exception: {e}\n")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("INVESTIGATION_FAILED") from e

        return None
