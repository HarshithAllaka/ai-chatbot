from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.exceptions.handlers import (
    register_exception_handlers,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting AI Chatbot API...")

    init_db()

    yield

    print("🛑 Shutting down AI Chatbot API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(api_router)

    return app


app = create_app()