import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.domain.ai.interfaces import LLMProviderInterface
from app.domain.ai.schemas import AIExtractionResult, EmailCategory, PriorityLevel
from app.core.logger import logger


class OpenAIProvider(LLMProviderInterface):
    """OpenAI GPT-4o implementation of LLMProviderInterface."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.model_name = "gpt-4o-mini"

    @property
    def provider_name(self) -> str:
        return "OPENAI"

    async def extract_opportunity(
        self,
        email_subject: str,
        email_body: str,
        sender: str
    ) -> AIExtractionResult:
        if not self.client:
            raise ValueError("OpenAI API Key is missing.")

        system_prompt = (
            "You are CareerFlow AI's Opportunity Intelligence Engine. "
            "Analyze the provided email and extract career-related opportunity metadata into strict structured JSON. "
            "Categories allowed: Course, Certificate, Company, Assessment, Interview, Hackathon, Internship, Event, Reminder, Ignore. "
            "Do NOT act like an email client. Act like a career data parser."
        )

        user_content = f"Sender: {sender}\nSubject: {email_subject}\nBody:\n{email_body[:4000]}"

        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format=AIExtractionResult,
                temperature=0.1
            )
            
            result = response.choices[0].message.parsed
            return result
        except Exception as e:
            logger.error("OpenAI Provider Extraction Failed", error=str(e))
            raise e
