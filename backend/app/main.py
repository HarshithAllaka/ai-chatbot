from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.app_name} API"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }