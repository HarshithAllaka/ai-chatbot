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

        embeddings = await self.generate_embeddings(
            [text]
        )

        return embeddings[0]

    async def generate_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        embeddings = []

        for start in range(
            0,
            len(texts),
            settings.embedding_batch_size,
        ):

            batch = texts[
                start:start + settings.embedding_batch_size
            ]

            response = (
                await self.client.aio.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=batch,
                )
            )

            batch_embeddings = [
                embedding.values
                for embedding in response.embeddings
            ]

            if len(batch_embeddings) != len(batch):
                raise ValueError(
                    "Embedding response count does not match "
                    "the request batch size."
                )

            embeddings.extend(batch_embeddings)

        return embeddings
