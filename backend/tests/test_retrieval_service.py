from types import SimpleNamespace

from app.services.retrieval_service import (
    RetrievalService,
)


def build_row(
    chunk_id: int,
    distance: float,
    keyword_score: float,
    hybrid_score: float,
):

    chunk = SimpleNamespace(
        id=chunk_id,
        document_id=1,
    )

    return (
        chunk,
        distance,
        keyword_score,
        hybrid_score,
    )


def build_service() -> RetrievalService:

    return RetrievalService.__new__(
        RetrievalService
    )


def test_build_retrieval_result_labels_match_types():

    service = build_service()

    rows = [
        build_row(1, 0.1, 0.3, 0.9),
        build_row(2, 0.15, 0.0, 0.8),
        build_row(3, 0.5, 0.2, 0.7),
        build_row(4, 0.5, 0.0, 0.6),
    ]

    chunks, diagnostics = (
        service._build_retrieval_result(
            rows
        )
    )

    assert [
        candidate.match_type
        for candidate in diagnostics.candidates
    ] == [
        "hybrid",
        "semantic",
        "keyword",
        "none",
    ]

    assert [item.chunk.id for item in chunks] == [
        1,
        2,
        3,
    ]

    assert diagnostics.threshold == 0.2
    assert diagnostics.accepted_count == 3
    assert diagnostics.rejected_count == 1
