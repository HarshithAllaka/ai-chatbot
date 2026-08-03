from contextlib import asynccontextmanager

from fastapi import FastAPI

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

    @app.get("/")
    def root():
        return {
            "message": f"Welcome to {settings.app_name}"
        }

    @app.get("/health")
    def health():
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    return app


app = create_app()