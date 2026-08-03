from fastapi import HTTPException

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(
        self,
        repository: UserRepository,
    ):
        self.repository = repository

    def create_user(
        self,
        user: UserCreate,
    ) -> User:
        existing_user = self.repository.get_by_email(
            user.email
        )

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )

        hashed_password = get_password_hash(
            user.password
        )

        return self.repository.create(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
        )