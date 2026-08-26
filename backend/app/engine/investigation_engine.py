import logging
from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.investigation import InvestigationResult

logger = logging.getLogger(__name__)

class InvestigationEngine:
    def __init__(self):
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY is not set. Gemini investigation will be disabled.")
            self.client = None
        else:
            self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def investigate(self, prompt: str) -> InvestigationResult | None:
        if not self.client:
            logger.warning("Cannot investigate: missing Gemini API key")
            return None
            
        logger.info(f"Invoking Gemini model: {self.model}")
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=InvestigationResult,
                        temperature=0.2, # Keep it analytical and deterministic
                    ),
                )
                
                result_json = response.text
                if not result_json:
                    logger.error("Empty response from Gemini")
                    return None
                    
                result = InvestigationResult.model_validate_json(result_json)
                return result
            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    logger.error(f"GEMINI_QUOTA_EXHAUSTED: {e}")
                    # Fail fast and return a specific status string inside a dummy result or raise
                    raise RuntimeError("GEMINI_QUOTA_EXHAUSTED") from e
                
                if attempt < max_retries - 1:
                    logger.warning(f"Error during Gemini investigation (Attempt {attempt + 1}): {e}. Retrying.")
                    import time
                    time.sleep(5)
                    continue
                logger.error(f"Error during Gemini investigation: {e}")
                return None
        return None
