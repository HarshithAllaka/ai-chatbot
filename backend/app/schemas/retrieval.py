from dataclasses import dataclass

from app.models.document_chunk import (
    DocumentChunk,
)


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    distance: float
    keyword_score: float
    hybrid_score: float


@dataclass
class RetrievalCandidate:
    chunk_id: int
    document_id: int
    rank: int
    distance: float
    keyword_score: float
    hybrid_score: float
    match_type: str
    included: bool


@dataclass
class RetrievalDiagnostics:
    candidate_count: int
    accepted_count: int
    rejected_count: int
    threshold: float
    best_distance: float | None
    embedding_duration_ms: float
    search_duration_ms: float
    reranking_duration_ms: float
    total_duration_ms: float
    reranking_used: bool
    reranking_skip_reason: str | None
    candidates: list[RetrievalCandidate]


@dataclass
class RetrievalResult:
    context: str
    chunks: list[RetrievedChunk]
    count: int
    diagnostics: RetrievalDiagnostics


@dataclass
class RerankingResult:
    chunks: list[RetrievedChunk]
    used: bool
    skip_reason: str | None
