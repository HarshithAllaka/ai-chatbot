from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        message: Message,
    ) -> Message:

        self.db.add(message)

        await self.db.commit()

        await self.db.refresh(message)

        return message