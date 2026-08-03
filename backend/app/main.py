from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings

from app.db.base import Base
from app.db.database import engine
import app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting AI Chatbot API...")
    Base.metadata.create_all(bind=engine)
    yield
    print("🛑 Shutting down AI Chatbot API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.include_router(api_router)

    return app


app = create_app()