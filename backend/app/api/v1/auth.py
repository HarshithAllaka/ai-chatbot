from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import (
    get_current_user,
    get_user_service,
)
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserCreate,
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
async def signup(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return await service.create_user(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    return await service.login(form_data)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user