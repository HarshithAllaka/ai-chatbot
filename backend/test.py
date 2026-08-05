import asyncio

from app.services.embedding_service import (
    EmbeddingService,
)


async def main():

    service = EmbeddingService()

    embedding = await service.generate_embedding(
        "Docker is a container platform."
    )

    print(type(embedding))

    print(len(embedding))

    print(embedding[:10])


asyncio.run(main())