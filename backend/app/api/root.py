from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": f"Welcome to {settings.app_name}"
    }