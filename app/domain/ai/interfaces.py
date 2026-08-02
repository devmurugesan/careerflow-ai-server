from abc import ABC, abstractmethod
from app.domain.ai.schemas import AIExtractionResult


class LLMProviderInterface(ABC):
    """Abstract Base Class for LLM Provider implementations (OpenAI, Gemini, Claude)."""
    
    @abstractmethod
    async def extract_opportunity(
        self,
        email_subject: str,
        email_body: str,
        sender: str
    ) -> AIExtractionResult:
        """Extracts structured opportunity details from raw email content."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the provider name identifier."""
        pass
