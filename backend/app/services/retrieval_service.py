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
from app.services.reranking_service import (
    RerankingService,
)


class RetrievalService:

    SIMILARITY_THRESHOLD = 0.35
    DISTANCE_MARGIN = 0.10

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

        self.reranking_service = (
            RerankingService()
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

        best_distance = (
            min(
                float(distance)
                for _, distance, _, _ in rows
            )
            if rows
            else None
        )

        threshold = (
            min(
                self.SIMILARITY_THRESHOLD,
                best_distance + self.DISTANCE_MARGIN,
            )
            if best_distance is not None
            else self.SIMILARITY_THRESHOLD
        )

        for rank, (
            chunk,
            distance,
            keyword_score,
            hybrid_score,
        ) in enumerate(
            rows,
            start=1,
        ):

            distance = float(distance)

            keyword_score = float(keyword_score)

            hybrid_score = float(hybrid_score)

            semantic_match = (
                distance <= threshold
            )

            keyword_match = (
                keyword_score > 0
            )

            match_type = (
                "hybrid"
                if semantic_match and keyword_match
                else "semantic"
                if semantic_match
                else "keyword"
                if keyword_match
                else "none"
            )

            included = (
                match_type != "none"
            )

            candidates.append(
                RetrievalCandidate(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    rank=rank,
                    distance=distance,
                    keyword_score=keyword_score,
                    hybrid_score=hybrid_score,
                    match_type=match_type,
                    included=included,
                )
            )

            if included:

                retrieved_chunks.append(
                    RetrievedChunk(
                        chunk=chunk,
                        distance=distance,
                        keyword_score=keyword_score,
                        hybrid_score=hybrid_score,
                    )
                )

        diagnostics = RetrievalDiagnostics(
            candidate_count=len(candidates),
            accepted_count=len(retrieved_chunks),
            rejected_count=(
                len(candidates)
                - len(retrieved_chunks)
            ),
            threshold=threshold,
            best_distance=best_distance,
            candidates=candidates,
        )

        return retrieved_chunks, diagnostics

    def _update_diagnostics(
        self,
        diagnostics: RetrievalDiagnostics,
        reranked_chunks: list[RetrievedChunk],
    ) -> None:

        selected_chunk_ids = {
            item.chunk.id
            for item in reranked_chunks
        }

        for candidate in diagnostics.candidates:

            candidate.included = (
                candidate.chunk_id
                in selected_chunk_ids
            )

        diagnostics.accepted_count = len(
            reranked_chunks
        )

        diagnostics.rejected_count = (
            diagnostics.candidate_count
            - diagnostics.accepted_count
        )

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
                "keyword_score": candidate.keyword_score,
                "hybrid_score": candidate.hybrid_score,
                "match_type": candidate.match_type,
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
            "best_distance=%s | "
            "results=%s",
            conversation_id,
            diagnostics.candidate_count,
            diagnostics.accepted_count,
            diagnostics.rejected_count,
            diagnostics.threshold,
            diagnostics.best_distance,
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
                question=question,
            )
        )

        retrieved_chunks, diagnostics = (
            self._build_retrieval_result(
                rows
            )
        )

        reranked_chunks = (
            await self.reranking_service.rerank(
                question,
                retrieved_chunks,
            )
        )

        self._update_diagnostics(
            diagnostics,
            reranked_chunks,
        )

        self._log_diagnostics(
            conversation_id,
            diagnostics,
        )

        context = self._build_context(
            reranked_chunks
        )

        return RetrievalResult(
            context=context,
            chunks=reranked_chunks,
            count=len(reranked_chunks),
            diagnostics=diagnostics,
        )
