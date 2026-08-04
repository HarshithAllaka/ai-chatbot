from google import genai

from app.core.config import settings
from app.core.logging import logger
from app.exceptions.ai import AIServiceError


class AIService:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    async def generate_response(
        self,
        user_message: str,
    ) -> str:

        try:

            response = await self.client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=user_message,
            )

            return response.text

        except Exception as e:

            logger.exception(
                "Gemini API Error"
            )

            raise AIServiceError(
                "AI service is currently unavailable. Please try again later."
            ) from e