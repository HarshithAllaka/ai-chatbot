from asyncio import Semaphore

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.services.document_service import (
    DocumentService,
)

document_processing_semaphore = Semaphore(
    settings.document_processing_concurrency
)


async def process_document_task(
    document_id: int,
) -> None:

    async with document_processing_semaphore:

        async with AsyncSessionLocal() as db:

            service = DocumentService(db)

            await service.process_document(
                document_id
            )
