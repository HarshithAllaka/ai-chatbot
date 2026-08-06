from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_user,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
)
from app.services.document_service import (
    DocumentService,
)
from app.tasks.document_tasks import (
    process_document_task,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(
        get_current_user
    ),
    db: AsyncSession = Depends(get_db),
):

    service = DocumentService(db)

    document = await service.upload_document(
        current_user.id,
        file,
    )

    background_tasks.add_task(
        process_document_task,
        document.id,
    )

    return document