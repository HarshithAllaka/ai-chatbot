from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_user,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
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
    "/conversations/{conversation_id}",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_document(
    conversation_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(
        get_current_user,
    ),
    db: AsyncSession = Depends(get_db),
):

    service = DocumentService(db)

    document = await service.upload_document(
        conversation_id=conversation_id,
        user_id=current_user.id,
        file=file,
    )

    background_tasks.add_task(
        process_document_task,
        document.id,
    )

    return document


@router.get(
    "",
    response_model=list[DocumentListResponse],
)
async def list_documents(
    current_user: User = Depends(
        get_current_user,
    ),
    db: AsyncSession = Depends(get_db),
):

    service = DocumentService(db)

    return await service.list_documents(
        current_user.id,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
)
async def get_document(
    document_id: int,
    current_user: User = Depends(
        get_current_user,
    ),
    db: AsyncSession = Depends(get_db),
):

    service = DocumentService(db)

    document = await service.get_document(
        document_id,
        current_user.id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document