from app.db.database import AsyncSessionLocal
from app.services.document_service import (
    DocumentService,
)


async def process_document_task(
    document_id: int,
) -> None:

    async with AsyncSessionLocal() as db:

        service = DocumentService(db)

        await service.process_document(
            document_id
        )