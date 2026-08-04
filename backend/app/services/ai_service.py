from google import genai

from app.core.config import settings


class AIService:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    async def generate_response(
        self,
        user_message: str,
    ) -> str:

        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
        )

        return response.text