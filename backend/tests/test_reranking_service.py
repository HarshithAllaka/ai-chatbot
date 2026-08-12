from types import SimpleNamespace

import pytest

from app.schemas.retrieval import RetrievedChunk
from app.services.reranking_service import (
    RerankingService,
)


class FakeAIService:

    def __init__(
        self,
        response: str,
    ):
        self.response = response
        self.called = False

    async def generate_reranking_response(
        self,
        prompt: str,
    ) -> str:

        self.called = True

        return self.response


def build_chunk(
    chunk_id: int,
    hybrid_score: float,
) -> RetrievedChunk:

    chunk = SimpleNamespace(
        id=chunk_id,
    )

    return RetrievedChunk(
        chunk=chunk,
        distance=0.2,
        keyword_score=0.1,
        hybrid_score=hybrid_score,
    )


def build_service(
    response: str = '{"chunk_ids": []}',
) -> tuple[
    RerankingService,
    FakeAIService,
]:

    service = RerankingService.__new__(
        RerankingService
    )

    fake_ai_service = FakeAIService(
        response
    )

    service.ai_service = fake_ai_service

    return service, fake_ai_service


@pytest.mark.asyncio
async def test_rerank_skips_when_no_candidates():

    service, fake_ai_service = build_service()

    result = await service.rerank(
        "What is the refund deadline?",
        [],
    )

    assert result.chunks == []
    assert result.used is False
    assert result.skip_reason == "no_candidates"
    assert fake_ai_service.called is False


@pytest.mark.asyncio
async def test_rerank_skips_when_one_candidate_exists():

    service, fake_ai_service = build_service()

    chunk = build_chunk(
        chunk_id=1,
        hybrid_score=0.8,
    )

    result = await service.rerank(
        "What is the refund deadline?",
        [chunk],
    )

    assert result.chunks == [chunk]
    assert result.used is False
    assert result.skip_reason == "single_candidate"
    assert fake_ai_service.called is False


@pytest.mark.asyncio
async def test_rerank_skips_when_top_score_dominates():

    service, fake_ai_service = build_service()

    top_chunk = build_chunk(
        chunk_id=1,
        hybrid_score=0.9,
    )

    second_chunk = build_chunk(
        chunk_id=2,
        hybrid_score=0.7,
    )

    result = await service.rerank(
        "What is the refund deadline?",
        [top_chunk, second_chunk],
    )

    assert result.chunks == [top_chunk]
    assert result.used is False
    assert result.skip_reason == "dominant_hybrid_score"
    assert fake_ai_service.called is False


@pytest.mark.asyncio
async def test_rerank_uses_valid_gemini_order_for_ambiguous_scores():

    service, fake_ai_service = build_service(
        '{"chunk_ids": [2, 1]}'
    )

    first_chunk = build_chunk(
        chunk_id=1,
        hybrid_score=0.8,
    )

    second_chunk = build_chunk(
        chunk_id=2,
        hybrid_score=0.72,
    )

    result = await service.rerank(
        "What is the refund deadline?",
        [first_chunk, second_chunk],
    )

    assert result.chunks == [
        second_chunk,
        first_chunk,
    ]
    assert result.used is True
    assert result.skip_reason is None
    assert fake_ai_service.called is True


def test_parse_chunk_ids_removes_invalid_and_duplicate_ids():

    service, _ = build_service()

    chunks = [
        build_chunk(1, 0.8),
        build_chunk(2, 0.7),
    ]

    chunk_ids = service._parse_chunk_ids(
        '{"chunk_ids": [2, 2, 999, 1]}',
        chunks,
    )

    assert chunk_ids == [2, 1]
