import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.retrieval import (
    RerankingResult,
    RetrievedChunk,
)
from app.services.retrieval_service import RetrievalService


@pytest.mark.asyncio
async def test_retrieve_context_cache_miss_then_hit():
    mock_db = AsyncMock()
    service = RetrievalService(mock_db)

    # Mock embedding service
    service.embedding_service = MagicMock()
    service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1, 0.2, 0.3]
    )

    # Mock document and chunk
    doc = Document(id=1, original_filename="test.pdf")
    chunk = DocumentChunk(
        id=10,
        document_id=1,
        chunk_index=0,
        content="Artificial intelligence in healthcare.",
    )
    chunk.document = doc

    # Mock repository search_chunks (returns row: chunk, distance, keyword_score, hybrid_score)
    service.repository = MagicMock()
    service.repository.search_chunks = AsyncMock(
        return_value=[(chunk, 0.15, 0.5, 0.8)]
    )

    # Mock reranking service
    retrieved_chunk = RetrievedChunk(
        chunk=chunk,
        distance=0.15,
        keyword_score=0.5,
        hybrid_score=0.8,
    )
    service.reranking_service = MagicMock()
    service.reranking_service.rerank = AsyncMock(
        return_value=RerankingResult(
            chunks=[retrieved_chunk],
            used=True,
            skip_reason=None,
        )
    )

    # In-memory dict simulating Redis key-value store
    redis_store = {}

    mock_redis = MagicMock()

    async def fake_get(key: str):
        return redis_store.get(key)

    async def fake_setex(key: str, ttl: int, val: bytes):
        redis_store[key] = val

    mock_redis.get = AsyncMock(side_effect=fake_get)
    mock_redis.setex = AsyncMock(side_effect=fake_setex)

    with patch("app.services.retrieval_service.get_redis_client", return_value=mock_redis):
        # 1. First call: Cache MISS
        result1 = await service.retrieve_context(
            conversation_id=42,
            question="What is AI in healthcare?",
        )

        assert result1.count == 1
        assert "Artificial intelligence in healthcare" in result1.context
        assert service.repository.search_chunks.call_count == 1
        assert service.reranking_service.rerank.call_count == 1
        assert mock_redis.setex.call_count == 1

        # 2. Second call with same question & conversation: Cache HIT
        result2 = await service.retrieve_context(
            conversation_id=42,
            question="What is AI in healthcare?",
        )

        assert result2.count == 1
        assert "Artificial intelligence in healthcare" in result2.context
        assert result2.chunks[0].chunk.document.original_filename == "test.pdf"

        # Search chunks and rerank must NOT have been called again!
        assert service.repository.search_chunks.call_count == 1
        assert service.reranking_service.rerank.call_count == 1


@pytest.mark.asyncio
async def test_retrieve_context_fail_open_on_redis_error():
    mock_db = AsyncMock()
    service = RetrievalService(mock_db)

    service.embedding_service = MagicMock()
    service.embedding_service.generate_embedding = AsyncMock(
        return_value=[0.1, 0.2]
    )

    doc = Document(id=2, original_filename="doc.pdf")
    chunk = DocumentChunk(
        id=20,
        document_id=2,
        chunk_index=0,
        content="Fail open test chunk content.",
    )
    chunk.document = doc

    service.repository = MagicMock()
    service.repository.search_chunks = AsyncMock(
        return_value=[(chunk, 0.1, 0.4, 0.7)]
    )

    retrieved_chunk = RetrievedChunk(
        chunk=chunk,
        distance=0.1,
        keyword_score=0.4,
        hybrid_score=0.7,
    )
    service.reranking_service = MagicMock()
    service.reranking_service.rerank = AsyncMock(
        return_value=RerankingResult(
            chunks=[retrieved_chunk],
            used=False,
            skip_reason="test",
        )
    )

    # Redis throws an unexpected exception
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(side_effect=RuntimeError("Redis connection dropped"))
    mock_redis.setex = AsyncMock(side_effect=RuntimeError("Redis connection dropped"))

    with patch("app.services.retrieval_service.get_redis_client", return_value=mock_redis):
        result = await service.retrieve_context(
            conversation_id=99,
            question="Any question?",
        )

        # Service still succeeds by falling back to DB & reranker
        assert result.count == 1
        assert "Fail open test chunk content." in result.context
        assert service.repository.search_chunks.call_count == 1
