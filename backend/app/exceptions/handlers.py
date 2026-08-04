from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.auth import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.exceptions.ai import AIServiceError

def register_exception_handlers(
    app: FastAPI,
) -> None:

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(
        request: Request,
        exc: UserAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "USER_ALREADY_EXISTS",
                    "message": "Email already registered",
                },
            },
        )

    @app.exception_handler(
        InvalidCredentialsError
    )
    async def invalid_credentials_handler(
        request: Request,
        exc: InvalidCredentialsError,
    ):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password",
                },
            },
        )

    @app.exception_handler(AIServiceError)
    async def ai_service_handler(
        request: Request,
        exc: AIServiceError,
    ):
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "AI_SERVICE_ERROR",
                    "message": str(exc),
                },
            },
        )