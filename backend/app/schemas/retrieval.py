from dataclasses import dataclass

from app.models.document_chunk import (
    DocumentChunk,
)


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    distance: float


@dataclass
class RetrievalResult:
    context: str
    chunks: list[RetrievedChunk]
    count: int