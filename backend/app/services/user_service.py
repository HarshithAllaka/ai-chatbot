from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.exceptions.auth import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserCreate


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
            raise UserAlreadyExistsError()

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
        form_data: OAuth2PasswordRequestForm,
    ) -> TokenResponse:
        user = self.repository.get_by_email(
            form_data.username,
        )

        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(
            form_data.password,
            user.hashed_password,
        ):
            raise InvalidCredentialsError()

        token = create_access_token(
            subject=str(user.id),
        )

        return TokenResponse(
            access_token=token,
        )