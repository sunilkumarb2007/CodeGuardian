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
            "temperature": 0.0,
            "max_tokens": 4096
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

        def _validate_diff_completeness(diff: str) -> bool:
            if not diff or not isinstance(diff, str):
                return False
            diff_str = diff.strip()
            if not ("---" in diff_str and "+++" in diff_str and "@@" in diff_str):
                return False
            lines = diff_str.splitlines()
            hunk_started = False
            has_changes = False
            for line in lines:
                if line.startswith("@@"):
                    hunk_started = True
                elif hunk_started:
                    if line.startswith("+") or line.startswith("-"):
                        has_changes = True
            return hunk_started and has_changes

        for attempt in range(max_retries):
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                logger.error('SARVAM_REQUEST_TIMEOUT: deadline already expired before attempt')
                raise RuntimeError('AI_TIMEOUT')

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
                        raise RuntimeError("AI_PROVIDER_ERROR")
                    elif resp.status_code == 429:
                        logger.error("SARVAM_REQUEST_FAILED: SARVAM_RATE_LIMITED")
                        raise RuntimeError("RATE_LIMIT_EXCEEDED")
                    elif resp.status_code in (400, 413, 422):
                        logger.error(f"SARVAM_REQUEST_FAILED: SARVAM_INVALID_REQUEST ({resp.status_code}) - {resp.text}")
                        raise RuntimeError("AI_INVALID_RESPONSE")
                    elif resp.status_code >= 500:
                        logger.error(f"SARVAM_REQUEST_FAILED: SARVAM_PROVIDER_ERROR ({resp.status_code})")
                        raise RuntimeError("AI_PROVIDER_ERROR")

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
                        f"SARVAM_RESPONSE_METADATA: response_status={resp.status_code} choices={len(choices)} "
                        f"finish_reason={finish_reason} content_present={content is not None} "
                        f"response_length={len(content) if content else 0} "
                        f"reasoning_present={reasoning is not None} "
                        f"reasoning_len={len(reasoning) if reasoning else 0} "
                        f"configured_output_limit=4096 elapsed_ms={duration_ms:.0f} "
                        f"attempt_number={attempt + 1}"
                    )

                    if content is None and tool_calls:
                        logger.error("SARVAM_REQUEST_FAILED: SARVAM_TOOL_CALL_RESPONSE")
                        raise RuntimeError("AI_INVALID_RESPONSE")

                    # 1. Detect Truncation Explicitly
                    is_truncated = (finish_reason == "length")

                    # If content is None or empty, try extracting valid JSON from reasoning_content
                    if not content and reasoning:
                        import re
                        json_blocks = re.findall(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', reasoning)
                        if json_blocks:
                            for blk in reversed(json_blocks):
                                try:
                                    parsed = InvestigationResult.model_validate_json(blk)
                                    if parsed.patch_candidate and _validate_diff_completeness(parsed.patch_candidate.diff):
                                        content = blk
                                        is_truncated = False
                                        logger.info("Successfully extracted complete InvestigationResult JSON from reasoning_content markdown block.")
                                        break
                                except Exception:
                                    pass
                        if not content:
                            start_brace = reasoning.find("{")
                            end_brace = reasoning.rfind("}")
                            if start_brace != -1 and end_brace > start_brace:
                                candidate = reasoning[start_brace:end_brace + 1]
                                try:
                                    parsed = InvestigationResult.model_validate_json(candidate)
                                    if parsed.patch_candidate and _validate_diff_completeness(parsed.patch_candidate.diff):
                                        content = candidate
                                        is_truncated = False
                                        logger.info("Successfully recovered complete InvestigationResult JSON from reasoning_content braces.")
                                except Exception:
                                    pass

                    # 2. If Truncated or Incomplete, invoke Bounded Recovery Path
                    if is_truncated or not content:
                        logger.warning(
                            f"SARVAM_TRUNCATION_DETECTED: finish_reason={finish_reason}, content_len={len(content) if content else 0}. "
                            f"Invoking compact truncation recovery attempt..."
                        )
                        if attempt < max_retries - 1:
                            recovery_payload = {
                                "model": self.model,
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": (
                                            "Your previous response was incomplete or truncated by the output token limit. "
                                            "Return ONLY a minimal, complete JSON object. "
                                            "Do NOT include markdown, preamble, or commentary. "
                                            "Do NOT repeat the repository analysis. "
                                            "The unified diff must be complete and valid for the affected file.\n\n"
                                            "Return strictly this minimal JSON structure:\n"
                                            "{\n"
                                            '  "root_cause": "<actual root cause summary>",\n'
                                            '  "root_cause_service": "<actual service name>",\n'
                                            '  "affected_file": "<actual file path from context>",\n'
                                            '  "line": 1,\n'
                                            '  "repair_summary": "<concise fix summary>",\n'
                                            '  "diff": "--- a/<file>\\n+++ b/<file>\\n@@ -1,1 +1,2 @@\\n+<fix>",\n'
                                            '  "confidence": 1.0\n'
                                            "}\n\n"
                                            f"Investigation Context:\n{prompt[:1500]}"
                                        )
                                    }
                                ],
                                "temperature": 0.0,
                                "max_tokens": 4096
                            }
                            rec_resp = client.post(endpoint, headers=headers, json=recovery_payload)
                            if rec_resp.status_code == 200:
                                rec_data = rec_resp.json()
                                rec_choice = rec_data.get("choices", [{}])[0]
                                rec_content = rec_choice.get("message", {}).get("content")
                                rec_reasoning = rec_choice.get("message", {}).get("reasoning_content")
                                rec_finish = rec_choice.get("finish_reason")
                                if not rec_content and rec_reasoning:
                                    start_b = rec_reasoning.find("{")
                                    end_b = rec_reasoning.rfind("}")
                                    if start_b != -1 and end_b > start_b:
                                        rec_content = rec_reasoning[start_b:end_b + 1]
                                if rec_content:
                                    try:
                                        rec_clean = rec_clean_str = rec_content.strip()
                                        if "```json" in rec_clean_str:
                                            parts = rec_clean_str.split("```json")
                                            rec_clean_str = parts[1].split("```")[0]
                                        elif "```" in rec_clean_str:
                                            parts = rec_clean_str.split("```")
                                            rec_clean_str = parts[1]
                                        
                                        start_b = rec_clean_str.find("{")
                                        end_b = rec_clean_str.rfind("}")
                                        if start_b != -1 and end_b > start_b:
                                            rec_clean_str = rec_clean_str[start_b:end_b + 1]
                                        
                                        rec_result = InvestigationResult.model_validate_json(rec_clean_str)
                                        if rec_result.patch_candidate and _validate_diff_completeness(rec_result.patch_candidate.diff):
                                            logger.info("SARVAM_TRUNCATION_RECOVERY_SUCCESS: Recovered valid InvestigationResult via compact schema.")
                                            return rec_result
                                    except Exception as ex:
                                        logger.warning(f"Recovery payload validation failed: {ex}")
                        
                        logger.error("SARVAM_REQUEST_FAILED: AI_OUTPUT_TRUNCATED")
                        raise RuntimeError("AI_OUTPUT_TRUNCATED")

                    content = content.strip()
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        parts = content.split("```")
                        if len(parts) >= 3:
                            content = parts[1]
                    
                    s_b = content.find("{")
                    e_b = content.rfind("}")
                    if s_b != -1 and e_b > s_b:
                        content = content[s_b:e_b + 1]
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

                    # Validate complete diff
                    if result.patch_candidate and not _validate_diff_completeness(result.patch_candidate.diff):
                        logger.warning("SARVAM_PATCH_INCOMPLETE: Candidate diff is structurally incomplete.")
                        if attempt < max_retries - 1:
                            continue
                        raise RuntimeError("AI_OUTPUT_TRUNCATED")

                    return result

                except httpx.HTTPStatusError as e:
                    logger.error(f"SARVAM_HTTP_STATUS_ERROR: {e.response.status_code}")
                    if e.response.status_code in (401, 403):
                        raise RuntimeError("AI_PROVIDER_ERROR")
                    elif e.response.status_code == 429:
                        raise RuntimeError("RATE_LIMIT_EXCEEDED")
                    elif e.response.status_code in (400, 413, 422):
                        raise RuntimeError("AI_INVALID_RESPONSE")
                    elif e.response.status_code >= 500:
                        raise RuntimeError("AI_PROVIDER_ERROR")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("AI_PROVIDER_ERROR")

                except httpx.TimeoutException:
                    elapsed_ms = (time.monotonic() - req_start) * 1000
                    logger.error(f"SARVAM_REQUEST_TIMEOUT: httpx timeout after {elapsed_ms:.0f}ms")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("AI_TIMEOUT")

                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    logger.error(f"SARVAM_SCHEMA_ERROR: Failed to parse Sarvam response: {e}")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("AI_SCHEMA_ERROR") from e

                except RuntimeError:
                    raise

                except Exception as e:
                    logger.error(f"Error during Sarvam investigation: {e}")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("AI_PROVIDER_ERROR") from e

        return None
