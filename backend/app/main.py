from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.root import router as root_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting AI Chatbot API...")
    yield
    print("🛑 Shutting down AI Chatbot API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.include_router(
        root_router,
        prefix="/api/v1",
        tags=["Root"],
    )

    app.include_router(
        health_router,
        prefix="/api/v1",
        tags=["Health"],
    )

    return app


app = create_app()