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
        messages: list[dict],
    ) -> str:

        try:

            response = await self.client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=messages,
            )

            return response.text

        except Exception as e:

            logger.exception(
                "Gemini API Error"
            )

            raise AIServiceError(
                "AI service is currently unavailable."
            ) from e

    async def stream_response(
        self,
        messages: list[dict],
    ):

        stream = await self.client.aio.models.generate_content_stream(
            model=settings.gemini_model,
            contents=messages,
        )

        async for chunk in stream:
            
            if chunk.text:
                yield chunk.text