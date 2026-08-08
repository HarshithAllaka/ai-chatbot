from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_repository import (
    DocumentRepository,
)
from app.schemas.retrieval import (
    RetrievalResult,
    RetrievedChunk,
)
from app.services.embedding_service import (
    EmbeddingService,
)


class RetrievalService:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.repository = (
            DocumentRepository(db)
        )

        self.embedding_service = (
            EmbeddingService()
        )

    async def retrieve_context(
        self,
        conversation_id: int,
        question: str,
    ) -> RetrievalResult:

        embedding = (
            await self.embedding_service.generate_embedding(
                question
            )
        )

        rows = (
            await self.repository.search_chunks(
                conversation_id=conversation_id,
                embedding=embedding,
            )
        )

        threshold = 0.35

        retrieved_chunks = []

        for chunk, distance in rows:

            if distance <= threshold:

                retrieved_chunks.append(
                    RetrievedChunk(
                        chunk=chunk,
                        distance=distance,
                    )
                )

        context = "\n\n".join(
            item.chunk.content
            for item in retrieved_chunks
        )

        return RetrievalResult(
            context=context,
            chunks=retrieved_chunks,
            count=len(retrieved_chunks),
        )