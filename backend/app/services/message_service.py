from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import (
    Message,
    MessageRole,
)
from app.repositories.message_repository import (
    MessageRepository,
)
from app.schemas.message import (
    ChatResponse,
    DocumentSource,
    MessageCreate,
)
from app.services.ai_service import AIService
from app.services.conversation_service import (
    ConversationService,
)
from app.services.retrieval_service import (
    RetrievalService,
)


class MessageService:

    CITATION_EXCERPT_LENGTH = 300

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.repository = MessageRepository(db)

        self.ai_service = AIService()

        self.conversation_service = (
            ConversationService(db)
        )

        self.retrieval_service = (
            RetrievalService(db)
        )

    async def _save_user_message(
        self,
        conversation_id: int,
        content: str,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )

        return await self.repository.create(
            message
        )

    async def _save_assistant_message(
        self,
        conversation_id: int,
        content: str,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
        )

        return await self.repository.create(
            message
        )

    async def _generate_title_if_needed(
        self,
        conversation_id: int,
        first_message: str,
    ) -> None:

        conversation = (
            await self.conversation_service.get_by_id(
                conversation_id
            )
        )

        if (
            conversation is not None
            and conversation.title == "New Chat"
        ):

            title = (
                await self.ai_service.generate_title(
                    first_message
                )
            )

            await self.conversation_service.update_title(
                conversation,
                title,
            )

    def _build_excerpt(
        self,
        content: str,
    ) -> str:

        normalized_content = " ".join(
            content.split()
        )

        if (
            len(normalized_content)
            <= self.CITATION_EXCERPT_LENGTH
        ):
            return normalized_content

        return (
            normalized_content[
                :self.CITATION_EXCERPT_LENGTH
            ].rstrip()
            + "..."
        )

    def _build_sources(
        self,
        retrieval_chunks,
    ) -> list[DocumentSource]:

        sources = []

        for retrieved in retrieval_chunks:

            chunk = retrieved.chunk

            document = chunk.document

            sources.append(
                DocumentSource(
                    document_id=document.id,
                    chunk_id=chunk.id,
                    filename=document.original_filename,
                    chunk_index=chunk.chunk_index,
                    excerpt=self._build_excerpt(
                        chunk.content
                    ),
                )
            )

        return sources

    async def send_message(
        self,
        conversation_id: int,
        data: MessageCreate,
    ) -> ChatResponse:

        user_message = (
            await self._save_user_message(
                conversation_id,
                data.content,
            )
        )

        await self._generate_title_if_needed(
            conversation_id,
            data.content,
        )

        history = (
            await self.repository.get_by_conversation(
                conversation_id
            )
        )

        retrieval = (
            await self.retrieval_service.retrieve_context(
                conversation_id=conversation_id,
                question=data.content,
            )
        )

        ai_response = (
            await self.ai_service.generate_chat_response(
                question=data.content,
                history=history,
                context=retrieval.context,
            )
        )

        assistant_message = (
            await self._save_assistant_message(
                conversation_id,
                ai_response,
            )
        )

        sources = self._build_sources(
            retrieval.chunks
        )

        return ChatResponse(
            user_message=user_message,
            assistant_message=assistant_message,
            sources=sources,
        )
