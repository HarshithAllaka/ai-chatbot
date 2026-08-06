from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_repository import (
    DocumentRepository,
)
from app.schemas.retrieval import (
    RetrievalResult,
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

        chunks = (
            await self.repository.search_chunks(
                conversation_id=conversation_id,
                embedding=embedding,
            )
        )

        context = "\n\n".join(
            chunk.content
            for chunk in chunks
        )

        return RetrievalResult(
            context=context,
            chunks=chunks,
            count=len(chunks),
        )