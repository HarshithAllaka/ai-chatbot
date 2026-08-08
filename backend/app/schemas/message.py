from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)

from app.models.message import MessageRole


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    role: MessageRole
    content: str
    created_at: datetime


class DocumentSource(BaseModel):
    document_id: int
    filename: str


class ChatResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    sources: list[DocumentSource]