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

    async def generate_title(
        self,
        message: str,
    ) -> str:

        prompt = f"""
        
        Generate a short conversation title.

        Rules:
        - Maximum 5 words
        - No quotation marks
        - No punctuation at the end
        - Only return the title

        User message:
        {message}
        """

        response = await self.client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        return response.text.strip()

    async def answer_with_context(
        self,
        question: str,
        context: str,
    ) -> str:

        prompt = f"""
        
        You are a helpful AI assistant.

        Answer ONLY using the provided context.

        If the answer cannot be found,
        say that the information is not available.

        Context:

        {context}

        Question:

        {question}
        """

        return await self.generate_response(
            prompt
        )