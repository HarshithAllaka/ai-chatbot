from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.security import decode_access_token
from app.db.database import get_db
from app.exceptions.auth import InvalidCredentialsError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


def get_user_repository(
    db=Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repository: UserRepository = Depends(get_user_repository),
) -> User:

    try:
        payload = decode_access_token(token)

        user_id = payload.get("sub")

        if user_id is None:
            raise InvalidCredentialsError()

    except JWTError:
        raise InvalidCredentialsError()

    user = await repository.get_by_id(
        int(user_id)
    )

    if user is None:
        raise InvalidCredentialsError()

    return user