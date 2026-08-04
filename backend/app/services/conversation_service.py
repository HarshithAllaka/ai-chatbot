from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.repositories.conversation_repository import (
    ConversationRepository,
)
from app.schemas.conversation import (
    ConversationCreate,
)


class ConversationService:

    def __init__(self, db: AsyncSession):
        self.repository = ConversationRepository(db)

    async def create_conversation(
        self,
        user_id: int,
        data: ConversationCreate,
    ):

        conversation = Conversation(
            title=data.title,
            user_id=user_id,
        )

        return await self.repository.create(
            conversation
        )

    async def get_conversations(
        self,
        user_id: int,
    ):

        return await self.repository.get_all_by_user(
            user_id
        )  