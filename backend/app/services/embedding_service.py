from google import genai

from app.core.config import settings


class EmbeddingService:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    async def generate_embedding(
        self,
        text: str,
    ) -> list[float]:

        response = await self.client.aio.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text,
        )

        return response.embeddings[0].values