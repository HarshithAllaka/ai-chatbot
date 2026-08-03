from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(
    prefix="/auth",
)


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=201,
)
def signup(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)

    service = UserService(repository)

    created_user = service.create_user(user)

    return created_user
