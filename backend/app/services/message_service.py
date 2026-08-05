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
from app.services.conversation_service import ConversationService


class MessageService:

    def __init__(self, db: AsyncSession):
        self.repository = MessageRepository(db)
        self.ai_service = AIService()
        self.conversation_service = ConversationService(db)

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

        # Get conversation
        conversation = await self.conversation_service.get_by_id(
            conversation_id
        )

        # Generate title only once
        if conversation.title == "New Chat":

            title = await self.ai_service.generate_title(
                data.content
            )

            await self.conversation_service.update_title(
                conversation,
                title,
            )

        # Load conversation history
        history = await self.repository.get_by_conversation(
            conversation_id
        )

        gemini_messages = []

        for message in history:

            role = (
                "model"
                if message.role == MessageRole.ASSISTANT
                else "user"
            )

            gemini_messages.append(
                {
                    "role": role,
                    "parts": [
                        {
                            "text": message.content,
                        }
                    ],
                }
            )

        # Generate AI response
        ai_response = await self.ai_service.generate_response(
            gemini_messages
        )

        # Save assistant response
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

    async def stream_message(
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

        await self.repository.create(
            user_message
        )

        # Get conversation
        conversation = await self.conversation_service.get_by_id(
            conversation_id
        )

        # Generate title only once
        if conversation.title == "New Chat":

            title = await self.ai_service.generate_title(
                data.content
            )

            await self.conversation_service.update_title(
                conversation,
                title,
            )

        # Load conversation history
        history = await self.repository.get_by_conversation(
            conversation_id
        )

        gemini_messages = []

        for message in history:

            role = (
                "model"
                if message.role == MessageRole.ASSISTANT
                else "user"
            )

            gemini_messages.append(
                {
                    "role": role,
                    "parts": [
                        {
                            "text": message.content,
                        }
                    ],
                }
            )

        # Stream AI response
        complete_response = ""

        async for chunk in self.ai_service.stream_response(
            gemini_messages
        ):

            complete_response += chunk

            yield chunk

        # Save assistant response
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=complete_response,
        )

        await self.repository.create(
            assistant_message
        )