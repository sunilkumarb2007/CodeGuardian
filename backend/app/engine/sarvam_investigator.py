import logging
import json
import time
import httpx
from typing import Optional

from app.core.config import settings
from app.schemas.investigation import InvestigationResult
from app.engine.investigator_provider import InvestigatorProvider

logger = logging.getLogger(__name__)

_MIN_ATTEMPT_TIMEOUT = 30.0   # seconds
_CONNECT_TIMEOUT = 10.0       # seconds

class SarvamInvestigator(InvestigatorProvider):
    def __init__(self):
        self.api_key = settings.sarvam_api_key or settings.openrouter_api_key
        self.model = settings.sarvam_model or settings.ai_model or "sarvam-105b"
        self.base_url = (settings.sarvam_base_url or settings.ai_base_url or "https://api.sarvam.ai").rstrip("/")

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def provider_name(self) -> str:
        return "sarvam"

    def investigate(self, prompt: str, deadline: Optional[float] = None, on_milestone = None) -> Optional[InvestigationResult]:
        if not self.api_key:
            logger.warning("Cannot investigate: missing Sarvam API key")
            raise RuntimeError("SARVAM_AUTH_FAILED")

        endpoint = f"{self.base_url}/v1/chat/completions"
        logger.info(f"Invoking Sarvam AI direct API: {endpoint} (model: {self.model})")

        headers = {
            "api-subscription-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Single user prompt with explicit directive to bypass internal chain of thought loop
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "You are an automated program repair engineer. "
                        "Do NOT write any chain-of-thought, reasoning steps, or internal monologue. "
                        "Immediately output ONLY the final JSON object conforming to the required InvestigationResult schema.\n\n"
                        f"{prompt}"
                    )
                }
            ],
            "response_format": {
                "type": "json_object"
            },
            "temperature": 0.0,
            "max_tokens": 8192
        }

        payload_bytes = len(json.dumps(payload).encode('utf-8'))
        prompt_chars = len(prompt)
        logger.info(f"SARVAM_REQUEST_SIZE: {payload_bytes} bytes (prompt length: {prompt_chars} chars)")
        logger.info(f"SARVAM_ENDPOINT: {endpoint}")

        max_retries = 2

        from app.core.execution_policy import ExecutionPolicy
        if deadline is None:
            deadline = time.monotonic() + ExecutionPolicy.AI_TOTAL_DEADLINE
            logger.warning("investigate() called without a shared deadline — using fresh budget")

        for attempt in range(max_retries):
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                logger.error('SARVAM_REQUEST_TIMEOUT: deadline already expired before attempt')
                raise RuntimeError('SARVAM_TIMEOUT')

            capped = min(remaining_time, ExecutionPolicy.AI_REQUEST_TIMEOUT)
            attempt_timeout = max(capped, _MIN_ATTEMPT_TIMEOUT)

            timeout = httpx.Timeout(
                attempt_timeout,
                connect=_CONNECT_TIMEOUT,
                read=attempt_timeout,
                write=10.0
            )
            logger.info(
                f"SARVAM_ATTEMPT {attempt + 1}/{max_retries}: "
                f"timeout={attempt_timeout:.1f}s remaining={remaining_time:.1f}s"
            )

            with httpx.Client(timeout=timeout) as client:
                req_start = time.monotonic()
                content = None
                try:
                    logger.info(f"SARVAM_CONNECTING: sending request to {endpoint}")
                    if on_milestone:
                        on_milestone("system", "Connecting to Sarvam AI", f"Connecting to {endpoint} ({self.model})...")

                    resp = client.post(endpoint, headers=headers, json=payload)
                    duration_ms = (time.monotonic() - req_start) * 1000
                    logger.info(f"SARVAM_CONNECTED: response received in {duration_ms:.0f}ms status={resp.status_code}")

                    if resp.status_code in (401, 403):
                        logger.error(f"SARVAM_REQUEST_FAILED: SARVAM_AUTH_FAILED ({resp.status_code})")
                        raise RuntimeError("SARVAM_AUTH_FAILED")
                    elif resp.status_code == 429:
                        logger.error("SARVAM_REQUEST_FAILED: SARVAM_RATE_LIMITED")
                        raise RuntimeError("SARVAM_RATE_LIMITED")
                    elif resp.status_code in (400, 413, 422):
                        logger.error(f"SARVAM_REQUEST_FAILED: SARVAM_INVALID_REQUEST ({resp.status_code}) - {resp.text}")
                        raise RuntimeError("SARVAM_INVALID_REQUEST")
                    elif resp.status_code >= 500:
                        logger.error(f"SARVAM_REQUEST_FAILED: SARVAM_PROVIDER_ERROR ({resp.status_code})")
                        raise RuntimeError("SARVAM_PROVIDER_ERROR")

                    resp.raise_for_status()

                    data = resp.json()
                    choices = data.get("choices", [])
                    usage = data.get("usage", {})
                    
                    choice = choices[0] if choices else {}
                    message = choice.get("message", {})
                    finish_reason = choice.get("finish_reason")
                    content = message.get("content")
                    reasoning = message.get("reasoning_content")
                    tool_calls = message.get("tool_calls")

                    # Log SAFE diagnostic metadata (NEVER log credentials or auth headers)
                    logger.info(
                        f"SARVAM_RESPONSE_METADATA: status=200 choices={len(choices)} "
                        f"finish_reason={finish_reason} content_present={content is not None} "
                        f"content_len={len(content) if content else 0} "
                        f"reasoning_present={reasoning is not None} "
                        f"reasoning_len={len(reasoning) if reasoning else 0} "
                        f"tool_calls_present={bool(tool_calls)} "
                        f"usage={usage}"
                    )

                    if content is None and tool_calls:
                        logger.error("SARVAM_REQUEST_FAILED: SARVAM_TOOL_CALL_RESPONSE")
                        raise RuntimeError("SARVAM_TOOL_CALL_RESPONSE")

                    # If content is None or empty, try extracting valid JSON from reasoning_content
                    if not content and reasoning:
                        import re
                        json_blocks = re.findall(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', reasoning)
                        if json_blocks:
                            for blk in reversed(json_blocks):
                                try:
                                    InvestigationResult.model_validate_json(blk)
                                    content = blk
                                    logger.info("Successfully extracted InvestigationResult JSON from reasoning_content markdown block.")
                                    break
                                except Exception:
                                    pass
                        if not content:
                            start_brace = reasoning.find("{")
                            end_brace = reasoning.rfind("}")
                            if start_brace != -1 and end_brace > start_brace:
                                candidate = reasoning[start_brace:end_brace + 1]
                                try:
                                    InvestigationResult.model_validate_json(candidate)
                                    content = candidate
                                    logger.info("Successfully recovered InvestigationResult JSON from reasoning_content braces.")
                                except Exception:
                                    pass

                    if not content and finish_reason == "length":
                        logger.error("SARVAM_REQUEST_FAILED: SARVAM_OUTPUT_TRUNCATED")
                        raise RuntimeError("SARVAM_OUTPUT_TRUNCATED")

                    if not content:
                        logger.error("SARVAM_REQUEST_FAILED: Empty content received from model")
                        raise RuntimeError("SARVAM_INVALID_RESPONSE")

                    if not content:
                        # Attempt to extract JSON from reasoning_content if content field was empty
                        if reasoning and "{" in reasoning and "}" in reasoning:
                            start_brace = reasoning.find("{")
                            end_brace = reasoning.rfind("}")
                            candidate = reasoning[start_brace:end_brace + 1]
                            try:
                                json.loads(candidate)
                                content = candidate
                                logger.info("Extracted JSON from reasoning_content.")
                            except Exception:
                                pass

                    if not content:
                        logger.error("SARVAM_REQUEST_FAILED: Empty content received from model")
                        raise RuntimeError("SARVAM_INVALID_RESPONSE")

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

                    # Handle string wrapping/trailing quote artifacts
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

                    logger.info("SARVAM_PARSE_STARTED")
                    parse_start = time.time()
                    result = InvestigationResult.model_validate_json(content)
                    parse_duration = (time.time() - parse_start) * 1000
                    logger.info(f"SARVAM_PARSE_COMPLETED duration_ms: {parse_duration:.2f}")

                    return result

                except httpx.HTTPStatusError as e:
                    logger.error(f"SARVAM_HTTP_STATUS_ERROR: {e.response.status_code}")
                    if e.response.status_code in (401, 403):
                        raise RuntimeError("SARVAM_AUTH_FAILED")
                    elif e.response.status_code == 429:
                        raise RuntimeError("SARVAM_RATE_LIMITED")
                    elif e.response.status_code in (400, 413, 422):
                        raise RuntimeError("SARVAM_INVALID_REQUEST")
                    elif e.response.status_code >= 500:
                        raise RuntimeError("SARVAM_PROVIDER_ERROR")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("SARVAM_PROVIDER_ERROR")

                except httpx.TimeoutException:
                    elapsed_ms = (time.monotonic() - req_start) * 1000
                    logger.error(f"SARVAM_REQUEST_TIMEOUT: httpx timeout after {elapsed_ms:.0f}ms")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("SARVAM_TIMEOUT")

                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    logger.error(f"SARVAM_SCHEMA_ERROR: Failed to parse Sarvam response: {e}")
                    if attempt < max_retries - 1:
                        logger.info("Attempting structured-output repair with feedback...")
                        payload["messages"].append({"role": "assistant", "content": content or ""})
                        payload["messages"].append({
                            "role": "user",
                            "content": (
                                f"Your previous response did not satisfy the required schema. "
                                f"Return ONLY a JSON object conforming to the supplied InvestigationResult schema. "
                                f"The validation failure was: {str(e)}"
                            )
                        })
                        continue
                    raise RuntimeError("SARVAM_SCHEMA_ERROR") from e

                except RuntimeError:
                    raise

                except Exception as e:
                    logger.error(f"Error during Sarvam investigation: {e}")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("SARVAM_PROVIDER_ERROR") from e

        return None
