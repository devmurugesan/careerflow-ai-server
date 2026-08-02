from typing import List
from app.core.config import settings
from app.domain.ai.interfaces import LLMProviderInterface
from app.infrastructure.ai_providers.openai_provider import OpenAIProvider
from app.infrastructure.ai_providers.gemini_provider import GeminiProvider
from app.infrastructure.ai_providers.claude_provider import ClaudeProvider
from app.core.logger import logger


class AIProviderFactory:
    """Factory and Router for LLM Providers with primary and fallback support."""

    @staticmethod
    def get_provider(provider_type: str) -> LLMProviderInterface:
        p_type = provider_type.upper()
        if p_type == "OPENAI":
            return OpenAIProvider()
        elif p_type == "GEMINI":
            return GeminiProvider()
        elif p_type == "CLAUDE":
            return ClaudeProvider()
        else:
            raise ValueError(f"Unknown AI Provider: {provider_type}")

    @staticmethod
    def get_fallback_chain() -> List[LLMProviderInterface]:
        """Returns primary provider followed by fallbacks."""
        chain = []
        try:
            chain.append(AIProviderFactory.get_provider(settings.PRIMARY_AI_PROVIDER))
        except Exception:
            pass

        try:
            fallback = AIProviderFactory.get_provider(settings.FALLBACK_AI_PROVIDER)
            if fallback.provider_name != settings.PRIMARY_AI_PROVIDER.upper():
                chain.append(fallback)
        except Exception:
            pass

        return chain
