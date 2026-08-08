from sqlalchemy import (
    Computed,
    ForeignKey,
    Integer,
    Text,
)

from sqlalchemy.dialects.postgresql import TSVECTOR

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from pgvector.sqlalchemy import Vector

from app.db.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', content)",
            persisted=True,
        ),
        nullable=True,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(3072),
        nullable=True,
    )

    document = relationship(
        "Document",
        back_populates="chunks",
    )
