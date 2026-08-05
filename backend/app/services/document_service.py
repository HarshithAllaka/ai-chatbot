from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import (
    Document,
    DocumentStatus,
)
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.services.pdf_service import (
    PDFService,
)


class DocumentService:

    def __init__(self, db: AsyncSession):
        self.repository = DocumentRepository(db)
        self.pdf_service = PDFService()

    async def upload_document(
        self,
        user_id: int,
        file: UploadFile,
    ) -> Document:

        # Validate PDF
        if file.content_type != "application/pdf":
            raise ValueError(
                "Only PDF files are allowed."
            )

        # Create uploads directory
        upload_dir = Path(settings.upload_dir)

        upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Generate unique filename
        extension = Path(file.filename).suffix

        unique_filename = (
            f"{uuid4()}{extension}"
        )

        storage_path = (
            upload_dir / unique_filename
        )

        # Save uploaded PDF
        with open(storage_path, "wb") as buffer:
            buffer.write(
                await file.read()
            )

        # Extract text from PDF
        extracted_text = (
            self.pdf_service.extract_text(
                str(storage_path)
            )
        )

        # Temporary verification
        print(
            "\n========== Extracted PDF ==========\n"
        )
        print(extracted_text)
        print(
            "\n===================================\n"
        )

        # Create document record
        document = Document(
            user_id=user_id,
            original_filename=file.filename,
            storage_path=str(storage_path),
            mime_type=file.content_type,
            file_size=storage_path.stat().st_size,
            status=DocumentStatus.PENDING,
        )

        return await self.repository.create(
            document
        )