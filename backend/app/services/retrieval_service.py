from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.schemas.retrieval import (
    RetrievalCandidate,
    RetrievalDiagnostics,
    RetrievalResult,
    RetrievedChunk,
)
from app.services.embedding_service import (
    EmbeddingService,
)


class RetrievalService:

    SIMILARITY_THRESHOLD = 0.35

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

    def _build_retrieval_result(
        self,
        rows,
    ) -> tuple[
        list[RetrievedChunk],
        RetrievalDiagnostics,
    ]:

        retrieved_chunks = []

        candidates = []

        for rank, (chunk, distance) in enumerate(
            rows,
            start=1,
        ):

            distance = float(distance)

            included = (
                distance <= self.SIMILARITY_THRESHOLD
            )

            candidates.append(
                RetrievalCandidate(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    rank=rank,
                    distance=distance,
                    included=included,
                )
            )

            if included:

                retrieved_chunks.append(
                    RetrievedChunk(
                        chunk=chunk,
                        distance=distance,
                    )
                )

        diagnostics = RetrievalDiagnostics(
            candidate_count=len(candidates),
            accepted_count=len(retrieved_chunks),
            rejected_count=(
                len(candidates)
                - len(retrieved_chunks)
            ),
            threshold=self.SIMILARITY_THRESHOLD,
            candidates=candidates,
        )

        return retrieved_chunks, diagnostics

    def _build_context(
        self,
        retrieved_chunks: list[RetrievedChunk],
    ) -> str:

        context_blocks = []

        for index, retrieved in enumerate(
            retrieved_chunks,
            start=1,
        ):

            chunk = retrieved.chunk

            document = chunk.document

            context_blocks.append(
                f"""
[Document {index}]
Filename: {document.original_filename}
Chunk: {chunk.chunk_index}

{chunk.content}
[/Document {index}]
""".strip()
            )

        return "\n\n---\n\n".join(
            context_blocks
        )

    def _log_diagnostics(
        self,
        conversation_id: int,
        diagnostics: RetrievalDiagnostics,
    ) -> None:

        candidate_summary = [
            {
                "rank": candidate.rank,
                "chunk_id": candidate.chunk_id,
                "document_id": candidate.document_id,
                "distance": candidate.distance,
                "included": candidate.included,
            }
            for candidate in diagnostics.candidates
        ]

        logger.info(
            "Retrieval diagnostics | "
            "conversation_id=%s | "
            "candidates=%s | "
            "accepted=%s | "
            "rejected=%s | "
            "threshold=%s | "
            "results=%s",
            conversation_id,
            diagnostics.candidate_count,
            diagnostics.accepted_count,
            diagnostics.rejected_count,
            diagnostics.threshold,
            candidate_summary,
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

        retrieved_chunks, diagnostics = (
            self._build_retrieval_result(
                rows
            )
        )

        self._log_diagnostics(
            conversation_id,
            diagnostics,
        )

        context = self._build_context(
            retrieved_chunks
        )

        return RetrievalResult(
            context=context,
            chunks=retrieved_chunks,
            count=len(retrieved_chunks),
            diagnostics=diagnostics,
        )