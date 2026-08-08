from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


class DocumentRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def create(
        self,
        document: Document,
    ) -> Document:

        self.db.add(document)

        await self.db.commit()

        await self.db.refresh(document)

        return document

    async def get_by_id(
        self,
        document_id: int,
    ) -> Document | None:

        stmt = (
            select(Document)
            .where(
                Document.id == document_id
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: int,
    ) -> list[Document]:

        stmt = (
            select(Document)
            .where(
                Document.user_id == user_id
            )
            .order_by(
                Document.created_at.desc()
            )
        )

        result = await self.db.execute(stmt)

        return list(
            result.scalars().all()
        )

    async def get_by_id_and_user(
        self,
        document_id: int,
        user_id: int,
    ) -> Document | None:

        stmt = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def add_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> None:

        self.db.add_all(chunks)

        await self.db.commit()

    async def update(
        self,
        document: Document,
    ) -> Document:

        await self.db.commit()

        await self.db.refresh(document)

        return document

    async def search_chunks(
        self,
        conversation_id: int,
        embedding: list[float],
        question: str,
        limit: int = 5,
    ):

        distance = (
            DocumentChunk.embedding.cosine_distance(
                embedding
            ).label("distance")
        )

        semantic_score = (
            1 - distance
        )

        query = (
            func.websearch_to_tsquery(
                "english",
                question,
            )
        )

        keyword_score = (
            func.ts_rank_cd(
                DocumentChunk.search_vector,
                query,
            ).label("keyword_score")
        )

        hybrid_score = (
            (
                semantic_score * 0.7
            )
            + (
                keyword_score * 0.3
            )
        ).label("hybrid_score")

        stmt = (
            select(
                DocumentChunk,
                distance,
                keyword_score,
                hybrid_score,
            )
            .options(
                selectinload(
                    DocumentChunk.document
                )
            )
            .join(Document)
            .where(
                Document.conversation_id
                == conversation_id
            )
            .order_by(
                hybrid_score.desc()
            )
            .limit(limit)
        )

        result = await self.db.execute(
            stmt
        )

        return result.all()
