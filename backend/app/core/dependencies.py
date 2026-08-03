from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

from app.core.config import settings

def get_user_repository(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    repository: UserRepository = Depends(
        get_user_repository
    ),
) -> UserService:
    return UserService(repository)

def get_settings():
    return settings