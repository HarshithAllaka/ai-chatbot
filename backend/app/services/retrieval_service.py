import hashlib
import json
from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.redis import get_redis_client
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.schemas.retrieval import (
    RetrievalCandidate,
    RetrievalDiagnostics,
    RetrievalResult,
    RerankingResult,
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

    def _get_duration_ms(
        self,
        start_time: float,
    ) -> float:

        return round(
            (perf_counter() - start_time) * 1000,
            2,
        )

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

    def _generate_cache_key(
        self,
        conversation_id: int,
        question: str,
    ) -> str:
        question_hash = hashlib.sha256(
            question.strip().lower().encode("utf-8")
        ).hexdigest()
        return f"retrieval:v1:{conversation_id}:{question_hash}"

    async def _get_cached_retrieval(
        self,
        conversation_id: int,
        question: str,
    ) -> RetrievalResult | None:
        if not settings.retrieval_cache_enabled:
            return None

        redis = get_redis_client()
        if redis is None:
            return None

        key = self._generate_cache_key(
            conversation_id,
            question,
        )

        try:
            raw = await redis.get(key)
            if raw is None:
                return None

            data = json.loads(
                raw.decode("utf-8")
                if isinstance(raw, bytes)
                else raw
            )
            return self._deserialize_retrieval_result(
                data
            )
        except Exception as exc:
            logger.warning(
                "Retrieval cache read error | error=%s",
                exc,
            )
            return None

    async def _set_cached_retrieval(
        self,
        conversation_id: int,
        question: str,
        result: RetrievalResult,
    ) -> None:
        if not settings.retrieval_cache_enabled:
            return

        redis = get_redis_client()
        if redis is None:
            return

        key = self._generate_cache_key(
            conversation_id,
            question,
        )

        try:
            data = self._serialize_retrieval_result(
                result
            )
            val = json.dumps(data).encode("utf-8")
            await redis.setex(
                key,
                settings.retrieval_cache_ttl,
                val,
            )
        except Exception as exc:
            logger.warning(
                "Retrieval cache write error | error=%s",
                exc,
            )

    def _serialize_retrieval_result(
        self,
        result: RetrievalResult,
    ) -> dict:
        return {
            "context": result.context,
            "count": result.count,
            "chunks": [
                {
                    "chunk_id": item.chunk.id,
                    "document_id": item.chunk.document_id,
                    "chunk_index": item.chunk.chunk_index,
                    "content": item.chunk.content,
                    "original_filename": (
                        item.chunk.document.original_filename
                        if item.chunk.document
                        else ""
                    ),
                    "distance": item.distance,
                    "keyword_score": item.keyword_score,
                    "hybrid_score": item.hybrid_score,
                }
                for item in result.chunks
            ],
            "diagnostics": {
                "candidate_count": result.diagnostics.candidate_count,
                "accepted_count": result.diagnostics.accepted_count,
                "rejected_count": result.diagnostics.rejected_count,
                "threshold": result.diagnostics.threshold,
                "best_distance": result.diagnostics.best_distance,
                "embedding_duration_ms": result.diagnostics.embedding_duration_ms,
                "search_duration_ms": result.diagnostics.search_duration_ms,
                "reranking_duration_ms": result.diagnostics.reranking_duration_ms,
                "total_duration_ms": result.diagnostics.total_duration_ms,
                "reranking_used": result.diagnostics.reranking_used,
                "reranking_skip_reason": result.diagnostics.reranking_skip_reason,
                "candidates": [
                    {
                        "chunk_id": c.chunk_id,
                        "document_id": c.document_id,
                        "rank": c.rank,
                        "distance": c.distance,
                        "keyword_score": c.keyword_score,
                        "hybrid_score": c.hybrid_score,
                        "match_type": c.match_type,
                        "included": c.included,
                    }
                    for c in result.diagnostics.candidates
                ],
            },
        }

    def _deserialize_retrieval_result(
        self,
        data: dict,
    ) -> RetrievalResult:
        chunks = []
        for item in data.get("chunks", []):
            doc = Document(
                id=item["document_id"],
                original_filename=item["original_filename"],
            )
            chunk = DocumentChunk(
                id=item["chunk_id"],
                document_id=item["document_id"],
                chunk_index=item["chunk_index"],
                content=item["content"],
            )
            chunk.document = doc
            chunks.append(
                RetrievedChunk(
                    chunk=chunk,
                    distance=item["distance"],
                    keyword_score=item["keyword_score"],
                    hybrid_score=item["hybrid_score"],
                )
            )

        diag_data = data.get("diagnostics", {})
        candidates = [
            RetrievalCandidate(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                rank=c["rank"],
                distance=c["distance"],
                keyword_score=c["keyword_score"],
                hybrid_score=c["hybrid_score"],
                match_type=c["match_type"],
                included=c["included"],
            )
            for c in diag_data.get("candidates", [])
        ]
        diagnostics = RetrievalDiagnostics(
            candidate_count=diag_data.get("candidate_count", 0),
            accepted_count=diag_data.get("accepted_count", 0),
            rejected_count=diag_data.get("rejected_count", 0),
            threshold=diag_data.get("threshold", 0.35),
            best_distance=diag_data.get("best_distance"),
            embedding_duration_ms=diag_data.get("embedding_duration_ms", 0.0),
            search_duration_ms=diag_data.get("search_duration_ms", 0.0),
            reranking_duration_ms=diag_data.get("reranking_duration_ms", 0.0),
            total_duration_ms=diag_data.get("total_duration_ms", 0.0),
            reranking_used=diag_data.get("reranking_used", False),
            reranking_skip_reason=diag_data.get("reranking_skip_reason"),
            candidates=candidates,
        )

        return RetrievalResult(
            context=data.get("context", ""),
            chunks=chunks,
            count=data.get("count", len(chunks)),
            diagnostics=diagnostics,
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
            embedding_duration_ms=0.0,
            search_duration_ms=0.0,
            reranking_duration_ms=0.0,
            total_duration_ms=0.0,
            reranking_used=False,
            reranking_skip_reason=None,
            candidates=candidates,
        )

        return retrieved_chunks, diagnostics

    def _update_diagnostics(
        self,
        diagnostics: RetrievalDiagnostics,
        reranking_result: RerankingResult,
    ) -> None:

        reranked_chunks = reranking_result.chunks

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

        diagnostics.reranking_used = (
            reranking_result.used
        )

        diagnostics.reranking_skip_reason = (
            reranking_result.skip_reason
        )

    def _update_timing_diagnostics(
        self,
        diagnostics: RetrievalDiagnostics,
        embedding_duration_ms: float,
        search_duration_ms: float,
        reranking_duration_ms: float,
        total_duration_ms: float,
    ) -> None:

        diagnostics.embedding_duration_ms = (
            embedding_duration_ms
        )

        diagnostics.search_duration_ms = (
            search_duration_ms
        )

        diagnostics.reranking_duration_ms = (
            reranking_duration_ms
        )

        diagnostics.total_duration_ms = (
            total_duration_ms
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
            "embedding_duration_ms=%s | "
            "search_duration_ms=%s | "
            "reranking_duration_ms=%s | "
            "reranking_used=%s | "
            "reranking_skip_reason=%s | "
            "total_duration_ms=%s | "
            "results=%s",
            conversation_id,
            diagnostics.candidate_count,
            diagnostics.accepted_count,
            diagnostics.rejected_count,
            diagnostics.threshold,
            diagnostics.best_distance,
            diagnostics.embedding_duration_ms,
            diagnostics.search_duration_ms,
            diagnostics.reranking_duration_ms,
            diagnostics.reranking_used,
            diagnostics.reranking_skip_reason,
            diagnostics.total_duration_ms,
            candidate_summary,
        )

    async def retrieve_context(
        self,
        conversation_id: int,
        question: str,
    ) -> RetrievalResult:

        total_start_time = perf_counter()

        cached_result = await self._get_cached_retrieval(
            conversation_id,
            question,
        )
        if cached_result is not None:
            total_duration_ms = self._get_duration_ms(total_start_time)
            cached_result.diagnostics.total_duration_ms = total_duration_ms
            logger.info(
                "Retrieval cache HIT | conversation_id=%s | duration_ms=%s",
                conversation_id,
                total_duration_ms,
            )
            return cached_result

        embedding_start_time = perf_counter()

        embedding = (
            await self.embedding_service.generate_embedding(
                question
            )
        )

        embedding_duration_ms = (
            self._get_duration_ms(
                embedding_start_time
            )
        )

        search_start_time = perf_counter()

        rows = (
            await self.repository.search_chunks(
                conversation_id=conversation_id,
                embedding=embedding,
                question=question,
            )
        )

        search_duration_ms = (
            self._get_duration_ms(
                search_start_time
            )
        )

        retrieved_chunks, diagnostics = (
            self._build_retrieval_result(
                rows
            )
        )

        reranking_start_time = perf_counter()

        reranking_result = (
            await self.reranking_service.rerank(
                question,
                retrieved_chunks,
            )
        )

        reranking_duration_ms = (
            self._get_duration_ms(
                reranking_start_time
            )
        )

        self._update_diagnostics(
            diagnostics,
            reranking_result,
        )

        self._update_timing_diagnostics(
            diagnostics,
            embedding_duration_ms,
            search_duration_ms,
            reranking_duration_ms,
            self._get_duration_ms(
                total_start_time
            ),
        )

        self._log_diagnostics(
            conversation_id,
            diagnostics,
        )

        context = self._build_context(
            reranking_result.chunks
        )

        retrieval_result = RetrievalResult(
            context=context,
            chunks=reranking_result.chunks,
            count=len(reranking_result.chunks),
            diagnostics=diagnostics,
        )

        await self._set_cached_retrieval(
            conversation_id,
            question,
            retrieval_result,
        )

        return retrieval_result
