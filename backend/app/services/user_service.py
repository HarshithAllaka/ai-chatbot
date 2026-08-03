from fastapi import HTTPException, status

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin


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
                status_code=status.HTTP_400_BAD_REQUEST,
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

    def login(
        self,
        credentials: UserLogin,
    ) -> TokenResponse:
        user = self.repository.get_by_email(
            credentials.email
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            credentials.password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        token = create_access_token(
            subject=user.email,
        )

        return TokenResponse(
            access_token=token,
        )