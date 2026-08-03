from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_user_service
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/auth",
)


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return service.create_user(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    credentials: UserLogin,
    service: UserService = Depends(get_user_service),
):
    return service.login(credentials)