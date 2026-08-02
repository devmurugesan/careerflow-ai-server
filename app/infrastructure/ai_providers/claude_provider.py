from anthropic import AsyncAnthropic
from app.core.config import settings
from app.domain.ai.interfaces import LLMProviderInterface
from app.domain.ai.schemas import AIExtractionResult
from app.core.logger import logger


class ClaudeProvider(LLMProviderInterface):
    """Anthropic Claude 3.5 Sonnet implementation of LLMProviderInterface."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None
        self.model_name = "claude-3-5-sonnet-20240620"

    @property
    def provider_name(self) -> str:
        return "CLAUDE"

    async def extract_opportunity(
        self,
        email_subject: str,
        email_body: str,
        sender: str
    ) -> AIExtractionResult:
        if not self.client:
            raise ValueError("Anthropic API Key is missing.")

        prompt = f"""
You are CareerFlow AI's Opportunity Intelligence Engine. Extract career opportunity metadata into JSON matching this exact structure:
{{
  "category": "Course|Certificate|Company|Assessment|Interview|Hackathon|Internship|Event|Reminder|Ignore",
  "platform_or_company": "...",
  "opportunity_title": "...",
  "current_status": "Registered|Started|In Progress|Completed|Assessment|Interview|Offer|Joined|...",
  "priority": "LOW|MEDIUM|HIGH|URGENT",
  "deadline": "ISO datetime or null",
  "event_date": "ISO datetime or null",
  "action_required": "string or null",
  "summary": "2-sentence summary",
  "confidence_score": 0.95
}}

Email Details:
Sender: {sender}
Subject: {email_subject}
Body: {email_body[:4000]}
Return ONLY raw valid JSON.
"""

        try:
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.content[0].text
            return AIExtractionResult.model_validate_json(raw_text)
        except Exception as e:
            logger.error("Claude Provider Extraction Failed", error=str(e))
            raise e
