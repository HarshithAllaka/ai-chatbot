from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import (
    Document,
    DocumentStatus,
)
from app.models.document_chunk import (
    DocumentChunk,
)
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.services.chunking_service import (
    ChunkingService,
)
from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.pdf_service import (
    PDFService,
)


class DocumentService:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.repository = (
            DocumentRepository(db)
        )

        self.pdf_service = PDFService()

        self.chunking_service = (
            ChunkingService()
        )

        self.embedding_service = (
            EmbeddingService()
        )

    async def upload_document(
        self,
        conversation_id: int,
        user_id: int,
        file: UploadFile,
    ) -> Document:

        if file.content_type != "application/pdf":
            raise ValueError(
                "Only PDF files are allowed."
            )

        upload_dir = Path(
            settings.upload_dir
        )

        upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        extension = Path(
            file.filename
        ).suffix

        unique_filename = (
            f"{uuid4()}{extension}"
        )

        storage_path = (
            upload_dir / unique_filename
        )

        with open(
            storage_path,
            "wb",
        ) as buffer:

            buffer.write(
                await file.read()
            )

        document = Document(
            user_id=user_id,
            conversation_id=conversation_id,
            original_filename=file.filename,
            storage_path=str(storage_path),
            mime_type=file.content_type,
            file_size=storage_path.stat().st_size,
            status=DocumentStatus.PENDING,
        )

        return await self.repository.create(
            document
        )

    async def process_document(
        self,
        document_id: int,
    ) -> None:

        document = (
            await self.repository.get_by_id(
                document_id
            )
        )

        if document is None:
            return

        try:

            document.status = (
                DocumentStatus.PROCESSING
            )

            await self.repository.update(
                document
            )

            extracted_text = (
                self.pdf_service.extract_text(
                    document.storage_path
                )
            )

            chunks = (
                self.chunking_service.split_text(
                    extracted_text
                )
            )

            document_chunks = []

            for index, chunk in enumerate(
                chunks
            ):

                embedding = (
                    await self.embedding_service.generate_embedding(
                        chunk
                    )
                )

                document_chunks.append(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        content=chunk,
                        embedding=embedding,
                    )
                )

            if document_chunks:

                await self.repository.add_chunks(
                    document_chunks
                )

            document.status = (
                DocumentStatus.COMPLETED
            )

            await self.repository.update(
                document
            )

        except Exception:

            document.status = (
                DocumentStatus.FAILED
            )

            await self.repository.update(
                document
            )

            raise

    async def list_documents(
        self,
        user_id: int,
    ) -> list[Document]:

        return await self.repository.get_by_user(
            user_id
        )

    async def get_document(
        self,
        document_id: int,
        user_id: int,
    ) -> Document | None:

        return await self.repository.get_by_id_and_user(
            document_id,
            user_id,
        )