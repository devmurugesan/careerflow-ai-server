import json
from google import genai
from google.genai import types
from app.core.config import settings
from app.domain.ai.interfaces import LLMProviderInterface
from app.domain.ai.schemas import AIExtractionResult
from app.core.logger import logger


class GeminiProvider(LLMProviderInterface):
    """Google Gemini 1.5 Flash implementation of LLMProviderInterface."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.model_name = "gemini-1.5-flash"

    @property
    def provider_name(self) -> str:
        return "GEMINI"

    async def extract_opportunity(
        self,
        email_subject: str,
        email_body: str,
        sender: str
    ) -> AIExtractionResult:
        if not self.client:
            raise ValueError("Gemini API Key is missing.")

        prompt = f"""
System: You are CareerFlow AI's Opportunity Intelligence Engine. Analyze the provided email and extract career-related opportunity metadata into strict structured JSON matching the requested schema.
Categories: Course, Certificate, Company, Assessment, Interview, Hackathon, Internship, Event, Reminder, Ignore.

Sender: {sender}
Subject: {email_subject}
Body:
{email_body[:4000]}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIExtractionResult,
                    temperature=0.1,
                ),
            )
            result = AIExtractionResult.model_validate_json(response.text)
            return result
        except Exception as e:
            logger.error("Gemini Provider Extraction Failed", error=str(e))
            raise e
