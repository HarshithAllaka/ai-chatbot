from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import (
    Message,
    MessageRole,
)
from app.repositories.message_repository import (
    MessageRepository,
)
from app.schemas.message import MessageCreate


class MessageService:

    def __init__(self, db: AsyncSession):
        self.repository = MessageRepository(db)

    async def send_message(
        self,
        conversation_id: int,
        data: MessageCreate,
    ):

        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=data.content,
        )

        user_message = await self.repository.create(
            user_message
        )

        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="Hello! I am your AI assistant. OpenAI integration comes in the next lesson.",
        )

        assistant_message = await self.repository.create(
            assistant_message
        )

        return [
            user_message,
            assistant_message,
        ]  