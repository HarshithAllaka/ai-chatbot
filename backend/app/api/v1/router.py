from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.root import router as root_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(
    root_router,
    tags=["Root"],
)

api_router.include_router(
    health_router,
    tags=["Health"],
)