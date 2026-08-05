from app.repositories.document_repository import (
    DocumentRepository,
)
from app.services.embedding_service import (
    EmbeddingService,
)


class RetrievalService:

    def __init__(self, db):

        self.repository = (
            DocumentRepository(db)
        )

        self.embedding_service = (
            EmbeddingService()
        )

    async def retrieve_context(
        self,
        question: str,
    ) -> str:

        embedding = (
            await self.embedding_service.generate_embedding(
                question
            )
        )

        chunks = (
            await self.repository.search_chunks(
                embedding
            )
        )

        return "\n\n".join(
            chunk.content
            for chunk in chunks
        )