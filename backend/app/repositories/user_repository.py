from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def create(
        self,
        email: str,
        full_name: str,
        hashed_password: str,
    ) -> User:
        db_user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
        )

        self.db.add(db_user)

        await self.db.commit()

        await self.db.refresh(db_user)

        return db_user

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:

        stmt = select(User).where(
            User.email == email
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:

        stmt = select(User).where(
            User.id == user_id
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()