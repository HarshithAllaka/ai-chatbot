from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        embedding: list[float],
        limit: int = 5,
    ):

        stmt = (
            select(DocumentChunk)
            .order_by(
                DocumentChunk.embedding.cosine_distance(
                    embedding
                )
            )
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        return result.scalars().all()