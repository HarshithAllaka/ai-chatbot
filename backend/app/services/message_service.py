from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import (
    Message,
    MessageRole,
)
from app.repositories.message_repository import (
    MessageRepository,
)
from app.schemas.message import MessageCreate
from app.services.ai_service import AIService


class MessageService:

    def __init__(self, db: AsyncSession):
        self.repository = MessageRepository(db)
        self.ai_service = AIService()

    async def send_message(
        self,
        conversation_id: int,
        data: MessageCreate,
    ):

        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=data.content,
        )

        user_message = await self.repository.create(
            user_message
        )

        # Generate AI response
        ai_response = await self.ai_service.generate_response(
            data.content
        )

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=ai_response,
        )

        assistant_message = await self.repository.create(
            assistant_message
        )

        return [
            user_message,
            assistant_message,
        ]