from dataclasses import dataclass

from app.models.document_chunk import (
    DocumentChunk,
)


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    distance: float


@dataclass
class RetrievalCandidate:
    chunk_id: int
    document_id: int
    rank: int
    distance: float
    included: bool


@dataclass
class RetrievalDiagnostics:
    candidate_count: int
    accepted_count: int
    rejected_count: int
    threshold: float
    best_distance: float | None
    candidates: list[RetrievalCandidate]


@dataclass
class RetrievalResult:
    context: str
    chunks: list[RetrievedChunk]
    count: int
    diagnostics: RetrievalDiagnostics
