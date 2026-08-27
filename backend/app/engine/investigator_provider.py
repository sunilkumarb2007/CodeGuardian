from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.investigation import InvestigationResult

class InvestigatorProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name used by this provider."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'google', 'openrouter')."""
        pass

    @abstractmethod
    def investigate(self, prompt: str) -> Optional[InvestigationResult]:
        """
        Executes the investigation prompt and returns a structured InvestigationResult.
        Must handle retries, rate limits, and fallback logic gracefully.
        """
        pass
