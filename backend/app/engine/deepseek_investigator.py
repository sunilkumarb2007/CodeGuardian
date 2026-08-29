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

class DeepSeekInvestigator(InvestigatorProvider):
    def __init__(self):
        self.api_key = settings.deepseek_api_key or settings.openrouter_api_key
        self.model = settings.deepseek_model or settings.ai_model or "deepseek-chat"
        self.base_url = (settings.deepseek_base_url or settings.ai_base_url or "https://api.deepseek.com").rstrip("/")

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def provider_name(self) -> str:
        return "deepseek"

    def investigate(self, prompt: str, deadline: Optional[float] = None, on_milestone = None) -> Optional[InvestigationResult]:
        if not self.api_key:
            logger.warning("Cannot investigate: missing DeepSeek API key")
            raise RuntimeError("INVESTIGATOR_NOT_CONFIGURED")

        logger.info(f"Invoking DeepSeek direct API: {self.base_url}/chat/completions (model: {self.model})")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Request structured JSON format
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": (
                        "You are an expert automated root-cause analysis and automated program repair engineer. "
                        "You MUST respond ONLY with valid JSON conforming to the requested InvestigationResult schema. "
                        "Do not include any conversational preamble or markdown code blocks outside of the valid JSON object."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "response_format": {
                "type": "json_object"
            },
            "temperature": 0.2
        }

        payload_bytes = len(json.dumps(payload).encode('utf-8'))
        prompt_chars = len(prompt)
        logger.info(f"DEEPSEEK_REQUEST_SIZE: {payload_bytes} bytes (prompt length: {prompt_chars} chars)")
        logger.info(f"DEEPSEEK_ENDPOINT: {self.base_url}/chat/completions")

        max_retries = 3

        from app.core.execution_policy import ExecutionPolicy
        if deadline is None:
            deadline = time.monotonic() + ExecutionPolicy.AI_TOTAL_DEADLINE
            logger.warning("investigate() called without a shared deadline — using fresh budget")

        for attempt in range(max_retries):
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                logger.error('DEEPSEEK_REQUEST_TIMEOUT: deadline already expired before attempt')
                raise RuntimeError('INVESTIGATION_TIMEOUT')

            capped = min(remaining_time, ExecutionPolicy.AI_REQUEST_TIMEOUT)
            attempt_timeout = max(capped, _MIN_ATTEMPT_TIMEOUT)

            timeout = httpx.Timeout(
                attempt_timeout,
                connect=_CONNECT_TIMEOUT,
                read=attempt_timeout,
                write=10.0
            )
            logger.info(
                f"DEEPSEEK_ATTEMPT {attempt + 1}/{max_retries}: "
                f"timeout={attempt_timeout:.1f}s remaining={remaining_time:.1f}s"
            )

            with httpx.Client(timeout=timeout) as client:
                req_start = time.monotonic()
                content = None
                try:
                    logger.info(f"DEEPSEEK_CONNECTING: opening stream to {self.base_url}")
                    if on_milestone:
                        on_milestone("system", "Connecting to DeepSeek", f"Connecting to {self.base_url} ({self.model})...")

                    with client.stream("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                        connect_ms = (time.monotonic() - req_start) * 1000
                        logger.info(
                            f"DEEPSEEK_CONNECTED: headers received in {connect_ms:.0f}ms "
                            f"status={response.status_code}"
                        )
                        if on_milestone:
                            on_milestone("system", "DeepSeek connected", f"HTTP {response.status_code} received in {connect_ms/1000:.1f}s. Waiting for model response...")

                        if response.status_code == 429:
                            logger.error("DEEPSEEK_REQUEST_FAILED: RATE_LIMITED")
                            raise RuntimeError("RATE_LIMITED")
                        elif response.status_code == 401:
                            logger.error("DEEPSEEK_REQUEST_FAILED: DEEPSEEK_AUTH_FAILED")
                            raise RuntimeError("DEEPSEEK_AUTH_FAILED")
                        elif response.status_code == 402:
                            logger.error("DEEPSEEK_REQUEST_FAILED: DEEPSEEK_CREDITS_EXHAUSTED")
                            raise RuntimeError("DEEPSEEK_CREDITS_EXHAUSTED")
                        elif response.status_code == 403:
                            logger.error("DEEPSEEK_REQUEST_FAILED: DEEPSEEK_AUTH_FAILED")
                            raise RuntimeError("DEEPSEEK_AUTH_FAILED")
                        elif response.status_code == 408:
                            logger.error(f"DEEPSEEK_REQUEST_TIMEOUT: connect_ms={connect_ms:.2f}")
                            raise RuntimeError("DEEPSEEK_TIMEOUT")
                        elif response.status_code >= 500:
                            logger.error(f"DEEPSEEK_REQUEST_FAILED: PROVIDER_ERROR {response.status_code}")
                            raise RuntimeError("DEEPSEEK_PROVIDER_ERROR")

                        response.raise_for_status()

                        # Read stream in chunks
                        logger.info("DEEPSEEK_READING_BODY: starting chunked read")
                        content_bytes = bytearray()
                        first_chunk = True
                        for chunk in response.iter_bytes(chunk_size=8192):
                            if first_chunk:
                                first_byte_ms = (time.monotonic() - req_start) * 1000
                                logger.info(f"DEEPSEEK_FIRST_BYTE: {first_byte_ms:.0f}ms")
                                if on_milestone:
                                    on_milestone("analysis", "First token received", f"Model generating response ({first_byte_ms/1000:.1f}s TTFT)...")
                                first_chunk = False
                            if time.monotonic() > deadline:
                                logger.error("DEEPSEEK_REQUEST_TIMEOUT: wall-clock deadline exceeded during stream read")
                                raise RuntimeError('DEEPSEEK_TIMEOUT')
                            content_bytes.extend(chunk)

                        body_ms = (time.monotonic() - req_start) * 1000
                        logger.info(f"DEEPSEEK_BODY_COMPLETE: {body_ms:.0f}ms body_size={len(content_bytes)}B")
                        if on_milestone:
                            on_milestone("output", "Model response complete", f"Stream complete ({len(content_bytes)/1024:.1f} KB in {body_ms/1000:.1f}s). Validating structured JSON...")

                        data = json.loads(content_bytes.decode('utf-8'))
                        content = data.get("choices", [{}])[0].get("message", {}).get("content")

                    if not content:
                        logger.error("DEEPSEEK_REQUEST_FAILED: Empty content")
                        raise RuntimeError("DEEPSEEK_EMPTY_RESPONSE")

                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                        if content.endswith("```"):
                            content = content[:-3]
                    content = content.strip()

                    # Handle cases where model wraps in quotes or has trailing quotes
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

                    logger.info("DEEPSEEK_PARSE_STARTED")
                    parse_start = time.time()
                    result = InvestigationResult.model_validate_json(content)
                    parse_duration = (time.time() - parse_start) * 1000
                    logger.info(f"DEEPSEEK_PARSE_COMPLETED duration_ms: {parse_duration:.2f}")

                    return result

                except httpx.HTTPStatusError as e:
                    err_msg = ""
                    try:
                        err_msg = e.response.read().decode('utf-8')
                    except Exception:
                        pass
                        
                    logger.error(f"DEEPSEEK_REQUEST_FAILED: HTTPStatusError {e.response.status_code} - {err_msg}")
                    if e.response.status_code == 402:
                        raise RuntimeError("DEEPSEEK_CREDITS_EXHAUSTED")
                    elif e.response.status_code == 429:
                        raise RuntimeError("RATE_LIMITED")
                    elif e.response.status_code in (401, 403):
                        raise RuntimeError("DEEPSEEK_AUTH_FAILED")
                    elif e.response.status_code >= 500:
                        raise RuntimeError("DEEPSEEK_PROVIDER_ERROR")
                        
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("DEEPSEEK_PROVIDER_ERROR")

                except httpx.TimeoutException:
                    elapsed_ms = (time.monotonic() - req_start) * 1000
                    logger.error(f"DEEPSEEK_REQUEST_TIMEOUT: httpx timeout after {elapsed_ms:.0f}ms")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("INVESTIGATION_TIMEOUT")

                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    logger.error(f"INVESTIGATION_SCHEMA_ERROR: Failed to parse DeepSeek response: {e}")
                    if attempt < max_retries - 1:
                        logger.info("Attempting structured-output repair...")
                        payload["messages"].append({"role": "assistant", "content": content or ""})
                        payload["messages"].append({
                            "role": "user",
                            "content": (
                                f"Your previous response did not satisfy the required schema. "
                                f"Return only a JSON object conforming to the supplied InvestigationResult schema. "
                                f"The validation failure was: {str(e)}"
                            )
                        })
                        continue
                    raise RuntimeError("INVESTIGATION_SCHEMA_ERROR") from e

                except RuntimeError:
                    raise

                except Exception as e:
                    logger.error(f"Error during DeepSeek investigation: {e}")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("INVESTIGATION_FAILED") from e

        return None
