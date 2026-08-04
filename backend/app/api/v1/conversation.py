from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
)
from app.services.conversation_service import (
    ConversationService,
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=201,
)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = ConversationService(db)

    return await service.create_conversation(
        current_user.id,
        data,
    )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = ConversationService(db)

    return await service.get_conversations(
        current_user.id
    )