import logging
import json
import time
import httpx
import concurrent.futures
from typing import Optional

from app.core.config import settings
from app.schemas.investigation import InvestigationResult
from app.engine.investigator_provider import InvestigatorProvider

logger = logging.getLogger(__name__)

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

    def investigate(self, prompt: str, deadline: Optional[float] = None) -> Optional[InvestigationResult]:
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
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "investigation_result",
                    "strict": True,
                    "schema": schema
                }
            },
            "temperature": 0.2
        }
        
        payload_bytes = len(json.dumps(payload).encode('utf-8'))
        prompt_chars = len(prompt)
        logger.info(f"CODEGUARDIAN_REQUEST_SIZE: {payload_bytes} bytes (prompt length: {prompt_chars} chars)")

        logger.info(f"OPENROUTER_REQUEST_STARTED")
        logger.info(f"timestamp: {time.time()}")
        max_retries = 2
        
        # Use caller-supplied deadline or create a fresh one (fallback only)
        from app.core.execution_policy import ExecutionPolicy
        if deadline is None:
            deadline = time.monotonic() + ExecutionPolicy.AI_TOTAL_DEADLINE
            logger.warning("investigate() called without a shared deadline — using fresh 180s budget")
        
        for attempt in range(max_retries):
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                logger.error('OPENROUTER_REQUEST_TIMEOUT\nduration_ms: 0')
                raise RuntimeError('INVESTIGATION_TIMEOUT')
                
            current_timeout = min(remaining_time, ExecutionPolicy.AI_REQUEST_TIMEOUT)
            timeout = httpx.Timeout(
                current_timeout, 
                connect=10.0, 
                read=current_timeout, 
                write=10.0
            )
            with httpx.Client(timeout=timeout) as client:
                try:
                    req_start = time.monotonic()
                    remaining_wall = deadline - time.monotonic()
                    if remaining_wall <= 0:
                        raise RuntimeError('INVESTIGATION_TIMEOUT')
                    
                    # Use streaming response to enforce hard wall-clock deadline on each chunk
                    with client.stream("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                        req_duration = (time.monotonic() - req_start) * 1000
                        logger.info(f"OPENROUTER_RESPONSE_STARTED\nduration_ms: {req_duration:.2f}")
                        
                        if response.status_code == 429:
                            logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: OPENROUTER_RATE_LIMIT")
                            raise RuntimeError("OPENROUTER_RATE_LIMIT")
                        elif response.status_code == 401:
                            logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: OPENROUTER_AUTH_FAILED")
                            raise RuntimeError("OPENROUTER_AUTH_FAILED")
                        elif response.status_code == 403:
                            logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: OPENROUTER_ACCESS_DENIED")
                            raise RuntimeError("OPENROUTER_ACCESS_DENIED")
                        elif response.status_code == 408:
                            logger.error(f"OPENROUTER_REQUEST_TIMEOUT\nduration_ms: {req_duration:.2f}")
                            raise RuntimeError("INVESTIGATION_TIMEOUT")
                        elif response.status_code >= 500:
                            logger.error(f"OPENROUTER_REQUEST_FAILED\nerror_type: OPENROUTER_PROVIDER_ERROR")
                            raise RuntimeError("OPENROUTER_PROVIDER_ERROR")
                            
                        response.raise_for_status()
                        
                        # Read body in chunks and check deadline
                        content_bytes = bytearray()
                        for chunk in response.iter_bytes(chunk_size=8192):
                            if time.monotonic() > deadline:
                                logger.error("OPENROUTER_REQUEST_TIMEOUT: Hard wall-clock deadline exceeded during stream read")
                                raise RuntimeError('INVESTIGATION_TIMEOUT')
                            content_bytes.extend(chunk)
                            
                        data = json.loads(content_bytes.decode('utf-8'))
                        content = data.get("choices", [{}])[0].get("message", {}).get("content")
                    
                    if not content:
                        logger.error("OPENROUTER_REQUEST_FAILED\nerror_type: Empty content")
                        raise RuntimeError("OPENROUTER_INVALID_RESPONSE")
                        
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                        if content.endswith("```"):
                            content = content[:-3]
                    content = content.strip()
                    
                    logger.info("OPENROUTER_PARSE_STARTED")
                    parse_start = time.time()
                    result = InvestigationResult.model_validate_json(content)
                    parse_duration = (time.time() - parse_start) * 1000
                    logger.info(f"OPENROUTER_PARSE_COMPLETED\nduration_ms: {parse_duration:.2f}")
                    
                    return result
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"OPENROUTER_REQUEST_FAILED\nerror_type: HTTPStatusError {e.response.status_code}")
                    with open("debug_or.txt", "a") as f:
                        f.write(f"HTTP Error: {e.response.status_code} - {e.response.text}\n")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("OPENROUTER_HTTP_ERROR")
                except httpx.TimeoutException as e:
                    logger.error(f"OPENROUTER_REQUEST_TIMEOUT\nduration_ms: {(time.time() - req_start) * 1000:.2f}")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("INVESTIGATION_TIMEOUT")
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    logger.error(f"INVESTIGATION_SCHEMA_ERROR: Failed to parse OpenRouter response: {e}")
                    if attempt < max_retries - 1:
                        logger.info("Attempting structured-output repair...")
                        # Append a repair prompt explicitly describing the validation failure
                        payload["messages"].append({"role": "assistant", "content": content})
                        payload["messages"].append({
                            "role": "user",
                            "content": f"Your previous response did not satisfy the required schema. Return only an object conforming to the supplied JSON Schema. The validation failure was: {str(e)}"
                        })
                        continue
                    raise RuntimeError("INVESTIGATION_SCHEMA_ERROR") from e
                except RuntimeError as e:
                    with open("debug_or.txt", "a") as f:
                        f.write(f"Runtime Error: {e}\n")
                    raise e
                except Exception as e:
                    logger.error(f"Error during OpenRouter investigation: {e}")
                    with open("debug_or.txt", "a") as f:
                        f.write(f"Exception: {e}\n")
                    if attempt < max_retries - 1:
                        continue
                    raise RuntimeError("INVESTIGATION_FAILED") from e
                    
        return None
